"""Unit tests for a11y_check.py: python3 -m unittest discover -s actions/a11y-check/tests

axe itself is replaced by tests/fake_axe.py (canned JSON), so these run without a browser.
The real axe run is exercised end to end by .github/workflows/actions-test.yml.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import a11y_check  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")
FAKE = "%s %s" % (sys.executable, os.path.join(HERE, "fake_axe.py"))


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = a11y_check.main(["--axe-cmd", FAKE] + list(argv))
    return code, out.getvalue()


class SiteCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, rel, text="<!doctype html><title>x</title>"):
        p = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p


class DiscoveryTests(SiteCase):
    def test_every_html_under_root_skipping_tooling_dirs(self):
        for rel in ("index.html", "a/b.html", "node_modules/x/y.html", ".git/z.html", "note.txt"):
            self.write(rel)
        self.assertEqual(a11y_check.discover_pages(self.tmp, []), ["a/b.html", "index.html"])

    def test_explicit_urls_get_index_for_directories(self):
        self.assertEqual(a11y_check.discover_pages(self.tmp, ["/", "docs/", "/x.html"]),
                         ["index.html", "docs/index.html", "x.html"])


class AllowlistTests(SiteCase):
    def test_missing_file_means_no_exceptions(self):
        self.assertEqual(a11y_check.load_allowlist(os.path.join(self.tmp, "nope.json")), [])

    def test_entry_without_reason_is_an_error(self):
        with self.assertRaises(a11y_check.CheckError) as cm:
            a11y_check.load_allowlist(os.path.join(FIXTURES, "allow-no-reason.json"))
        self.assertIn("missing reason", str(cm.exception))

    def test_not_an_allow_object(self):
        p = self.write("a.json", "[]")
        with self.assertRaises(a11y_check.CheckError):
            a11y_check.load_allowlist(p)

    def test_selector_and_page_globs(self):
        e = [{"rule": "label", "selector": "#f-*", "reason": "r", "page": "docs/*"}]
        self.assertIsNotNone(a11y_check.is_allowed(e, "docs/a.html", "label", "#f-1"))
        self.assertIsNone(a11y_check.is_allowed(e, "index.html", "label", "#f-1"))
        self.assertIsNone(a11y_check.is_allowed(e, "docs/a.html", "image-alt", "#f-1"))


class EvaluateTests(unittest.TestCase):
    def test_only_serious_and_critical_block(self):
        res = [{"url": "http://h/p.html", "violations": [
            {"id": "a", "impact": "serious", "nodes": [{"target": ["#x"]}]},
            {"id": "b", "impact": "moderate", "nodes": [{"target": ["#y"]}]},
            {"id": "c", "impact": "minor", "nodes": [{"target": ["#z"]}]}]}]
        findings, allowed, _ = a11y_check.evaluate(res, [], "")
        self.assertEqual([f["rule"] for f in findings], ["a"])
        self.assertEqual(allowed, [])

    def test_nested_shadow_targets_are_joined(self):
        res = [{"url": "http://h/", "violations": [
            {"id": "a", "impact": "critical", "nodes": [{"target": [["host", "#inner"]]}]}]}]
        findings, _, _ = a11y_check.evaluate(res, [], "")
        self.assertEqual(findings[0]["selector"], "host #inner")
        self.assertEqual(findings[0]["page"], "index.html")


class EndToEndWithFakeAxe(SiteCase):
    def test_clean_site_passes(self):
        self.write("index.html")
        code, out = run("--root", self.tmp)
        self.assertEqual(code, 0, out)
        self.assertIn("0 violations", out)

    def test_violations_fail_and_are_explained(self):
        self.write("bad.html")
        code, out = run("--root", self.tmp)
        self.assertEqual(code, 1, out)
        self.assertIn("VIOLATION bad.html", out)
        self.assertIn("#logo", out)
        self.assertIn("https://dequeuniversity.com/rules/axe/4.14/image-alt", out)
        self.assertIn("2 violations", out)  # the moderate one does not count

    def test_allow_listed_violations_pass_and_unused_entry_warns(self):
        self.write("bad.html")
        allow = self.write(".a11y-allow.json", json.dumps({"allow": [
            {"rule": "image-alt", "selector": "#logo", "reason": "decorative"},
            {"rule": "label", "selector": "#email", "reason": "labelled by widget"},
            {"rule": "color-contrast", "selector": ".gone", "reason": "stale"}]}))
        code, out = run("--root", self.tmp)  # default allow-list name is found inside root
        self.assertEqual(code, 0, out)
        self.assertIn("0 violations, 2 allowed", out)
        self.assertIn("matched nothing", out)
        self.assertTrue(os.path.isfile(allow))

    def test_allow_entry_without_reason_fails_the_run(self):
        self.write("index.html")
        code, out = run("--root", self.tmp, "--allowlist", os.path.join(FIXTURES, "allow-no-reason.json"))
        self.assertEqual(code, 2, out)
        self.assertIn("missing reason", out)

    def test_empty_root_is_a_tooling_error_not_a_pass(self):
        code, out = run("--root", self.tmp)
        self.assertEqual(code, 2, out)

    def test_missing_explicit_page_is_an_error(self):
        self.write("index.html")
        code, out = run("--root", self.tmp, "--urls", "nope.html")
        self.assertEqual(code, 2, out)

    def test_axe_failure_is_an_error_not_a_pass(self):
        self.write("index.html")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = a11y_check.main(["--root", self.tmp, "--axe-cmd", "%s -c pass" % sys.executable])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
