#!/usr/bin/env python3
"""Accessibility check: serve a built site or static root and run axe-core on each page.

Fails (exit 1) on any violation of impact serious or critical, at the chosen WCAG level,
that is not on the allow-list. Exit 2 means the check itself could not run (bad
arguments, bad allow-list, axe or the browser failed), never "the site is fine".

Python 3.8+, standard library only. The browser side is @axe-core/cli, run with npx.
See README.md for why that tool and that pin.
"""
import argparse
import fnmatch
import functools
import http.server
import json
import os
import shlex
import subprocess
import sys
import threading
import urllib.parse

# Pinned: the version is part of the check's behaviour (the rule set ships inside axe-core).
AXE_CLI = "@axe-core/cli@4.14.0"

STANDARDS = {
    "wcag2a": ["wcag2a"],
    "wcag2aa": ["wcag2a", "wcag2aa"],
    "wcag21a": ["wcag2a", "wcag21a"],
    "wcag21aa": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"],
    "wcag22aa": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"],
}
BLOCKING = ("serious", "critical")
SKIP_DIRS = {"node_modules", ".git", ".github"}


class CheckError(Exception):
    """The check could not run (exit 2)."""


def discover_pages(root, urls):
    """Page paths (posix, relative to root, no leading slash) to test."""
    if urls:
        pages = []
        for u in urls:
            u = u.strip().lstrip("/")
            if u == "" or u.endswith("/"):
                u += "index.html"
            pages.append(u)
        return pages
    pages = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if name.lower().endswith((".html", ".htm")):
                rel = os.path.relpath(os.path.join(dirpath, name), root)
                pages.append(rel.replace(os.sep, "/"))
    return sorted(pages)


def load_allowlist(path):
    """Entries: {rule, selector, reason[, page]}. A missing file is an empty list; an
    entry without a reason is an error, so an exception is always explained."""
    if not path or not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        raise CheckError("cannot read allow-list %s: %s" % (path, exc))
    entries = data.get("allow") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise CheckError('allow-list %s must be {"allow": [ ... ]}' % path)
    problems = []
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            problems.append("entry %d is not an object" % i)
            continue
        for key in ("rule", "selector", "reason"):
            if not isinstance(e.get(key), str) or not e[key].strip():
                problems.append("entry %d (%s): missing %s" % (i, e.get("rule", "?"), key))
    if problems:
        raise CheckError("allow-list %s is invalid:\n  %s" % (path, "\n  ".join(problems)))
    return entries


def is_allowed(entries, page, rule, selector):
    """Return the matching entry, or None. selector and page accept glob patterns."""
    for e in entries:
        if e["rule"] != rule:
            continue
        if not fnmatch.fnmatchcase(selector, e["selector"]):
            continue
        if e.get("page") and not fnmatch.fnmatchcase(page, e["page"]):
            continue
        return e
    return None


def evaluate(results, entries, base_url):
    """Split axe results into blocking findings and allowed ones.

    Returns (findings, allowed, used) where findings and allowed are lists of dicts and
    used is the set of allow-list entry indexes that matched something."""
    findings, allowed, used = [], [], set()
    for res in results:
        url = res.get("url", "")
        page = urllib.parse.urlparse(url).path.lstrip("/") or "index.html"
        for v in res.get("violations", []):
            if v.get("impact") not in BLOCKING:
                continue
            for node in v.get("nodes", []):
                target = node.get("target") or []
                selector = " ".join(t if isinstance(t, str) else " ".join(t) for t in target)
                item = {
                    "page": page, "rule": v.get("id", "?"), "impact": v.get("impact"),
                    "selector": selector, "help": v.get("help", ""), "helpUrl": v.get("helpUrl", ""),
                }
                hit = is_allowed(entries, page, item["rule"], selector)
                if hit is not None:
                    used.add(entries.index(hit))
                    item["reason"] = hit["reason"]
                    allowed.append(item)
                else:
                    findings.append(item)
    return findings, allowed, used


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(root):
    handler = functools.partial(_QuietHandler, directory=root)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def run_axe(axe_cmd, urls, tags, chromedriver):
    cmd = list(axe_cmd) + urls + [
        "--stdout", "--tags", ",".join(tags),
        "--chrome-options", "no-sandbox,disable-dev-shm-usage",
    ]
    if chromedriver:
        cmd += ["--chromedriver-path", chromedriver]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    out = proc.stdout.strip()
    try:
        data = json.loads(out)
    except ValueError:
        raise CheckError("axe produced no JSON (exit %d):\n%s\n%s" % (proc.returncode, out[-2000:], proc.stderr[-2000:]))
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or len(data) != len(urls):
        raise CheckError("axe returned %s results for %d pages" % (len(data) if isinstance(data, list) else "?", len(urls)))
    return data


def find_chromedriver():
    """GitHub-hosted runners ship a chromedriver that matches their Chrome (CHROMEWEBDRIVER)."""
    base = os.environ.get("CHROMEWEBDRIVER")
    if base:
        for name in ("chromedriver", "chromedriver.exe"):
            p = os.path.join(base, name)
            if os.path.isfile(p):
                return p
    return None


def write_output(**values):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            for k, v in values.items():
                fh.write("%s=%s\n" % (k, v))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=".", help="directory to serve (built dist/ or a plain-HTML repo root)")
    ap.add_argument("--urls", default="", help="paths to test, newline or comma separated (default: every .html under root)")
    ap.add_argument("--allowlist", default=".a11y-allow.json", help="allow-list file; relative paths are tried inside root, then the working directory")
    ap.add_argument("--standard", default="wcag22aa", choices=sorted(STANDARDS))
    ap.add_argument("--axe-cmd", default="npx --yes " + AXE_CLI, help="command that runs axe (override for tests)")
    args = ap.parse_args(argv)

    try:
        root = os.path.abspath(args.root)
        if not os.path.isdir(root):
            raise CheckError("root %s is not a directory" % args.root)
        urls = [u for u in args.urls.replace(",", "\n").split("\n") if u.strip()]
        pages = discover_pages(root, urls)
        if not pages:
            raise CheckError("no .html pages under %s" % args.root)
        missing = [p for p in pages if not os.path.isfile(os.path.join(root, p))]
        if missing:
            raise CheckError("pages not found under %s: %s" % (args.root, ", ".join(missing)))

        allow_path = args.allowlist
        if allow_path and not os.path.isabs(allow_path):
            inside = os.path.join(root, allow_path)
            allow_path = inside if os.path.isfile(inside) else allow_path
        entries = load_allowlist(allow_path)

        server = serve(root)
        try:
            base = "http://127.0.0.1:%d/" % server.server_address[1]
            results = run_axe(shlex.split(args.axe_cmd), [base + urllib.parse.quote(p) for p in pages],
                              STANDARDS[args.standard], find_chromedriver())
        finally:
            server.shutdown()
        findings, allowed, used = evaluate(results, entries, base)
    except CheckError as exc:
        print("::error::a11y-check could not run: %s" % exc)
        write_output(pages=0, violations=0, allowed=0)
        return 2

    for i, e in enumerate(entries):
        if i not in used:
            print("::warning::allow-list entry matched nothing and can be removed: %s %s" % (e["rule"], e["selector"]))
    for a in allowed:
        print("allowed   %s  %s  %s  (%s)" % (a["page"], a["rule"], a["selector"], a["reason"]))
    for f in findings:
        print("::error file=%s::%s [%s] %s at %s" % (f["page"], f["rule"], f["impact"], f["help"], f["selector"]))
        print("VIOLATION %s  [%s] %s  %s\n          %s\n          %s" % (
            f["page"], f["impact"], f["rule"], f["selector"], f["help"], f["helpUrl"]))
    print("a11y-check: %d pages, standard %s, %d violations, %d allowed" % (
        len(pages), args.standard, len(findings), len(allowed)))
    write_output(pages=len(pages), violations=len(findings), allowed=len(allowed))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
