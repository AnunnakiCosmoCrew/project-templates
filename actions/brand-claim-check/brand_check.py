#!/usr/bin/env python3
"""Brand-and-claim check: grep a built site or a source tree against a JSON rules file.

Standard library only (Python 3.8+). No YAML, no third-party packages.

    python3 brand_check.py --rules brand-rules.json [--root dist] [--format text|github]

Exit status: 1 when any rule with severity "error" (the default) is violated,
0 otherwise. Rules with severity "warn" are reported but never fail the run.

The rules file schema is documented in README.md next to this script. Short form:

    {
      "root": "dist",                       # scan root, relative to the rules file (default ".")
      "ignore": [".git/**", "node_modules/**"],   # added to the built-in ignores
      "rules": [
        {"id": "no-street", "kind": "banned", "pattern": "yal[ıi]kent", "paths": ["**/*.html"],
         "exclude": ["drafts/**"], "allow": ["exact string removed before matching"],
         "severity": "error", "why": "The registered office is a home (LUVITA.md)."},
        {"id": "attribution", "kind": "required", "pattern": "a brand of <a href=\\"https://luvita\\.tr/\\"",
         "paths": ["**/*.html"], "why": "luvita-docs ADR 0001"},
        {"id": "no-cname", "kind": "file-banned", "paths": ["/CNAME"], "why": "domain not registered yet"},
        {"id": "root-page", "kind": "file-required", "paths": ["/index.html"], "why": "adr/0005"},
        {"id": "tr-en-parity", "kind": "pair", "left": "", "right": "en/", "paths": ["*.html"],
         "why": "both locales for every page"}
      ]
    }

Glob semantics follow .gitignore: a pattern without "/" matches the basename at any depth,
a leading "/" anchors to the scan root, "**" spans directories, "*" never crosses "/".
Every regex is compiled case-insensitively unless "flags" says otherwise ("" = case-sensitive).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Dict, Iterable, List, Optional, Tuple

BUILTIN_IGNORES = [".git/**", "node_modules/**", "**/node_modules/**", ".DS_Store"]
KINDS = {"banned", "required", "file-banned", "file-required", "pair"}
SEVERITIES = {"error", "warn"}
FLAG_MAP = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL, "x": re.VERBOSE}


class RulesError(Exception):
    """A malformed rules file. Reported as a configuration error, exit 2."""


# ----------------------------------------------------------------------------- globs


def glob_to_regex(pattern: str) -> "re.Pattern[str]":
    """Translate a .gitignore-style glob into a regex over a posix, root-relative path."""
    anchored = pattern.startswith("/")
    if anchored:
        pattern = pattern[1:]
    basename_only = "/" not in pattern
    out = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            if pattern[i : i + 3] == "**/":
                out.append("(?:.*/)?")
                i += 3
                continue
            if pattern[i : i + 2] == "**":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        elif c == "[":
            j = pattern.find("]", i + 1)
            if j == -1:
                out.append(re.escape(c))
            else:
                out.append(pattern[i : j + 1])
                i = j
        else:
            out.append(re.escape(c))
        i += 1
    body = "".join(out)
    if basename_only and not anchored:
        return re.compile(r"(?:^|.*/)" + body + r"$")
    return re.compile(r"^" + body + r"$")


class Matcher:
    def __init__(self, patterns: Iterable[str]):
        self.patterns = list(patterns)
        self.regexes = [glob_to_regex(p) for p in self.patterns]

    def __call__(self, rel: str) -> bool:
        return any(r.match(rel) for r in self.regexes)

    def __bool__(self) -> bool:
        return bool(self.regexes)


# ----------------------------------------------------------------------------- rules


def compile_flags(spec: Optional[str]) -> int:
    if spec is None:
        return re.IGNORECASE
    flags = 0
    for ch in spec:
        if ch not in FLAG_MAP:
            raise RulesError(f"unknown regex flag {ch!r}")
        flags |= FLAG_MAP[ch]
    return flags


class Rule:
    def __init__(self, raw: Dict, index: int):
        if not isinstance(raw, dict):
            raise RulesError(f"rule #{index} is not an object")
        self.id = str(raw.get("id") or f"rule-{index}")
        self.kind = raw.get("kind")
        if self.kind not in KINDS:
            raise RulesError(f"rule {self.id}: kind must be one of {sorted(KINDS)}, got {self.kind!r}")
        self.why = str(raw.get("why") or "").strip()
        if not self.why:
            raise RulesError(f"rule {self.id}: 'why' is required — say which rule or ADR this enforces")
        self.severity = raw.get("severity", "error")
        if self.severity not in SEVERITIES:
            raise RulesError(f"rule {self.id}: severity must be 'error' or 'warn'")
        paths = raw.get("paths")
        if not isinstance(paths, list) or not paths or not all(isinstance(p, str) for p in paths):
            raise RulesError(f"rule {self.id}: 'paths' must be a non-empty list of globs")
        self.paths = Matcher(paths)
        self.exclude = Matcher(raw.get("exclude") or [])
        self.allow: List[str] = list(raw.get("allow") or [])
        if not all(isinstance(a, str) and a for a in self.allow):
            raise RulesError(f"rule {self.id}: 'allow' must be a list of non-empty strings")
        self.regex: Optional["re.Pattern[str]"] = None
        if self.kind in ("banned", "required"):
            pattern = raw.get("pattern")
            if not isinstance(pattern, str) or not pattern:
                raise RulesError(f"rule {self.id}: 'pattern' (regex) is required for kind {self.kind}")
            try:
                self.regex = re.compile(pattern, compile_flags(raw.get("flags")))
            except re.error as exc:
                raise RulesError(f"rule {self.id}: bad regex: {exc}") from exc
        if self.kind == "pair":
            self.left = str(raw.get("left", ""))
            self.right = raw.get("right")
            if not isinstance(self.right, str) or not self.right:
                raise RulesError(f"rule {self.id}: 'right' (a directory prefix such as 'en/') is required for kind pair")
            self.left = self.left.strip("/")
            self.right = self.right.strip("/")
            if self.left == self.right:
                raise RulesError(f"rule {self.id}: 'left' and 'right' must differ")

    def applies_to(self, rel: str) -> bool:
        return self.paths(rel) and not self.exclude(rel)

    def scrub(self, text: str) -> str:
        """Blank out the allow-listed exact strings so they cannot match a banned pattern."""
        for literal in self.allow:
            if literal in text:
                text = text.replace(literal, " " * len(literal))
        return text


class Finding:
    def __init__(self, rule: Rule, path: str, line: int, message: str):
        self.rule = rule
        self.path = path
        self.line = line
        self.message = message

    def render(self, fmt: str) -> str:
        label = "warning" if self.rule.severity == "warn" else "error"
        where = f"{self.path}:{self.line}" if self.line else self.path
        text = f"[{self.rule.id}] {self.message} — {self.rule.why}"
        if fmt == "github":
            loc = f"file={self.path}" + (f",line={self.line}" if self.line else "")
            # "::" inside the message would end the annotation early.
            safe = text.replace("\n", " ").replace("::", ": :")
            return f"::{label} {loc},title=brand-check {self.rule.id}::{safe}"
        return f"{where}: {label}: {text}"


# ----------------------------------------------------------------------------- scanning


def load_rules(path: str) -> Tuple[str, Matcher, List[Rule]]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except FileNotFoundError:
        raise RulesError(f"rules file not found: {path}")
    except json.JSONDecodeError as exc:
        raise RulesError(f"{path}: invalid JSON: {exc}")
    if not isinstance(doc, dict):
        raise RulesError(f"{path}: top level must be an object")
    raw_rules = doc.get("rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise RulesError(f"{path}: 'rules' must be a non-empty list")
    rules = [Rule(r, i) for i, r in enumerate(raw_rules)]
    ids = [r.id for r in rules]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise RulesError(f"{path}: duplicate rule ids: {', '.join(dupes)}")
    root = doc.get("root", ".")
    if not isinstance(root, str):
        raise RulesError(f"{path}: 'root' must be a string")
    ignores = doc.get("ignore") or []
    if not isinstance(ignores, list) or not all(isinstance(p, str) for p in ignores):
        raise RulesError(f"{path}: 'ignore' must be a list of globs")
    return root, Matcher(BUILTIN_IGNORES + ignores), rules


def walk(root: str, ignored: Matcher) -> List[str]:
    files: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace(os.sep, "/")
        rel_dir = "" if rel_dir == "." else rel_dir + "/"
        # Prune ignored directories early (".git/**" matches ".git/anything").
        dirnames[:] = sorted(d for d in dirnames if not ignored(rel_dir + d + "/x") and not ignored(rel_dir + d))
        for name in sorted(filenames):
            rel = rel_dir + name
            if not ignored(rel):
                files.append(rel)
    return files


def is_binary(data: bytes) -> bool:
    return b"\x00" in data


def read_text(path: str) -> Optional[str]:
    with open(path, "rb") as fh:
        data = fh.read()
    if is_binary(data[:8192]):
        return None
    return data.decode("utf-8", errors="replace")


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def excerpt(text: str, start: int, end: int, width: int = 60) -> str:
    snippet = text[start:end]
    if len(snippet) > width:
        snippet = snippet[: width - 1] + "…"
    return snippet.replace("\n", "\\n")


def scan(root: str, ignored: Matcher, rules: List[Rule]) -> List[Finding]:
    findings: List[Finding] = []
    files = walk(root, ignored)
    text_rules = [r for r in rules if r.kind in ("banned", "required")]
    cache: Dict[str, Optional[str]] = {}

    for rel in files:
        applicable = [r for r in text_rules if r.applies_to(rel)]
        if not applicable:
            continue
        if rel not in cache:
            cache[rel] = read_text(os.path.join(root, rel))
        text = cache[rel]
        if text is None:
            continue  # binary
        for rule in applicable:
            assert rule.regex is not None
            if rule.kind == "banned":
                haystack = rule.scrub(text)
                for m in rule.regex.finditer(haystack):
                    findings.append(
                        Finding(rule, rel, line_of(haystack, m.start()), f"banned: {excerpt(haystack, m.start(), m.end())!r}")
                    )
            else:  # required
                if not rule.regex.search(text):
                    findings.append(Finding(rule, rel, 0, f"required pattern not found: /{rule.regex.pattern}/"))

    for rule in rules:
        if rule.kind == "file-banned":
            for rel in files:
                if rule.applies_to(rel):
                    findings.append(Finding(rule, rel, 0, "file must not exist"))
        elif rule.kind == "file-required":
            if not any(rule.applies_to(rel) for rel in files):
                findings.append(Finding(rule, root_label(root), 0, f"no file matches {rule_paths(rule)}"))
        elif rule.kind == "pair":
            findings.extend(check_pair(rule, files, root))
    return findings


def root_label(root: str) -> str:
    rel = os.path.relpath(root)
    return rel if rel else "."


def rule_paths(rule: Rule) -> str:
    return ", ".join(rule.paths.patterns)


def check_pair(rule: Rule, files: List[str], root: str) -> List[Finding]:
    """Every file under `left` that matches `paths` has a twin under `right`, and vice versa."""
    out: List[Finding] = []
    left_prefix = rule.left + "/" if rule.left else ""
    right_prefix = rule.right + "/" if rule.right else ""

    # When one side is nested in the other (left "" and right "en/"), keep the nested
    # subtree out of the outer side's listing.
    left_files = {}
    for rel in files:
        if not rel.startswith(left_prefix):
            continue
        if right_prefix and rel.startswith(right_prefix) and right_prefix.startswith(left_prefix):
            continue
        inner = rel[len(left_prefix) :]
        if rule.paths(inner) and not rule.exclude(rel):
            left_files[inner] = rel
    right_files = {}
    for rel in files:
        if not rel.startswith(right_prefix):
            continue
        if left_prefix and rel.startswith(left_prefix) and left_prefix.startswith(right_prefix) and left_prefix != right_prefix:
            continue
        inner = rel[len(right_prefix) :]
        if rule.paths(inner) and not rule.exclude(rel):
            right_files[inner] = rel

    for inner, rel in sorted(left_files.items()):
        if inner not in right_files:
            out.append(Finding(rule, rel, 0, f"has no counterpart {right_prefix}{inner}"))
    for inner, rel in sorted(right_files.items()):
        if inner not in left_files:
            out.append(Finding(rule, rel, 0, f"has no counterpart {left_prefix}{inner}"))
    return out


# ----------------------------------------------------------------------------- cli


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Brand-and-claim check (banned/required patterns over a tree).")
    ap.add_argument("--rules", default="brand-rules.json", help="rules file (default: brand-rules.json)")
    ap.add_argument("--root", default=None, help="scan root; overrides 'root' in the rules file")
    ap.add_argument("--format", choices=("text", "github"), default=None, help="output format (auto: github under GITHUB_ACTIONS)")
    ap.add_argument("--quiet", action="store_true", help="print findings and the summary only")
    args = ap.parse_args(argv)

    fmt = args.format or ("github" if os.environ.get("GITHUB_ACTIONS") == "true" else "text")
    try:
        rules_root, ignored, rules = load_rules(args.rules)
    except RulesError as exc:
        print(f"brand-check: configuration error: {exc}", file=sys.stderr)
        return 2

    root = args.root if args.root is not None else os.path.join(os.path.dirname(os.path.abspath(args.rules)), rules_root)
    root = os.path.normpath(root)
    if not os.path.isdir(root):
        print(f"brand-check: scan root is not a directory: {root} (build the site first?)", file=sys.stderr)
        return 2

    findings = scan(root, ignored, rules)
    errors = [f for f in findings if f.rule.severity == "error"]
    warnings = [f for f in findings if f.rule.severity == "warn"]

    if not args.quiet:
        print(f"brand-check: {len(rules)} rules over {os.path.relpath(root) or '.'} ({args.rules})")
    for f in findings:
        print(f.render(fmt))
    summary = f"brand-check: {len(errors)} error(s), {len(warnings)} warning(s)"
    if fmt == "github" and errors:
        print(f"::error title=brand-check::{summary}")
    print(summary)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
