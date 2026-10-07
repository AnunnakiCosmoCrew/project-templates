"""Unit tests for brand_check.py: python3 -m unittest discover -s actions/brand-claim-check/tests"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import brand_check  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")
RULES = os.path.join(FIXTURES, "rules.json")


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = brand_check.main(list(argv))
    return code, out.getvalue()


class GlobTests(unittest.TestCase):
    def match(self, pattern, path):
        return bool(brand_check.glob_to_regex(pattern).match(path))

    def test_basename_pattern_matches_at_any_depth(self):
        self.assertTrue(self.match("*.html", "index.html"))
        self.assertTrue(self.match("*.html", "en/deep/index.html"))
        self.assertTrue(self.match("CNAME", "CNAME"))
        self.assertFalse(self.match("CNAME", "docs/CNAME.md"))

    def test_leading_slash_anchors_to_root(self):
        self.assertTrue(self.match("/index.html", "index.html"))
        self.assertFalse(self.match("/index.html", "en/index.html"))

    def test_double_star_spans_directories_and_single_star_does_not(self):
        self.assertTrue(self.match("**/*.md", "README.md"))
        self.assertTrue(self.match("**/*.md", "docs/a/b.md"))
        self.assertTrue(self.match("docs/**", "docs/a/b.md"))
        self.assertTrue(self.match("docs/*.md", "docs/b.md"))
        self.assertFalse(self.match("docs/*.md", "docs/a/b.md"))

    def test_question_mark_and_character_class(self):
        self.assertTrue(self.match("file?.txt", "file1.txt"))
        self.assertTrue(self.match("en/[a-c]*.html", "en/about.html"))
        self.assertFalse(self.match("en/[a-c]*.html", "en/index.html"))

    def test_negated_class_and_classes_never_cross_directories(self):
        self.assertTrue(self.match("/[!a]*.html", "b.html"))
        self.assertFalse(self.match("/[!a]*.html", "a.html"))
        self.assertFalse(self.match("/[!a]*.html", "x/b.html"))
        self.assertFalse(self.match("/a[/]b", "a/b"))


class ScanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code, cls.out = run("--rules", RULES, "--format", "text")

    def test_exit_status_is_one_on_errors(self):
        self.assertEqual(self.code, 1, self.out)

    def test_banned_pattern_reports_file_and_line(self):
        self.assertIn("index.html:6: error: [no-street]", self.out)

    def test_exclude_glob_skips_drafts(self):
        self.assertNotIn("drafts/draft.html", self.out)

    def test_allow_strings_hide_legal_blocks_only(self):
        self.assertNotIn("[no-city]", self.out, "JSON-LD city was allow-listed")
        self.assertNotIn("[no-enerji]", self.out, "legal name was allow-listed")

    def test_required_pattern_reports_missing_pages(self):
        self.assertIn("about.html: error: [attribution]", self.out)
        self.assertIn("en/index.html: error: [attribution]", self.out)
        self.assertNotIn("index.html:0: error: [attribution]", self.out)

    def test_negative_lookahead_regex_works(self):
        self.assertIn("en/index.html:4: error: [holder]", self.out)

    def test_warn_rules_are_reported_but_do_not_fail(self):
        self.assertIn("about.html:2: warning: [no-timing]", self.out)
        self.assertIn("warning: [sitemap]", self.out)

    def test_file_rules(self):
        self.assertIn("CNAME: error: [no-cname] file must not exist", self.out)
        self.assertNotIn("[root-page]", self.out)

    def test_pair_rule_reports_missing_twins_in_both_directions(self):
        self.assertIn("about.html: error: [parity] has no counterpart en/about.html", self.out)

    def test_binary_files_are_skipped(self):
        self.assertNotIn("blob.bin", self.out)

    def test_why_is_quoted_with_every_finding(self):
        self.assertIn("— the registered office is a home", self.out)

    def test_summary_counts(self):
        self.assertIn("brand-check: 7 error(s), 2 warning(s)", self.out)


class CliTests(unittest.TestCase):
    def test_github_format_emits_annotations(self):
        code, out = run("--rules", RULES, "--format", "github")
        self.assertEqual(code, 1)
        # Annotation paths are workspace-relative (GITHUB_WORKSPACE, else the cwd), not root-relative.
        rel = os.path.relpath(os.path.join(FIXTURES, "site"), os.getcwd()).replace(os.sep, "/")
        self.assertIn(f"::error file={rel}/index.html,line=6,title=brand-check no-street::", out)
        self.assertIn(f"::warning file={rel}/about.html,line=2,title=brand-check no-timing::", out)

    def test_root_override_and_clean_tree_exit_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "index.html"), "w", encoding="utf-8") as fh:
                fh.write('<footer>© 2026 CosmoCrew — a brand of <a href="https://luvita.tr/">Luvita Teknoloji Ltd. Şti.</a></footer>')
            os.makedirs(os.path.join(tmp, "en"))
            with open(os.path.join(tmp, "en", "index.html"), "w", encoding="utf-8") as fh:
                fh.write('<footer>© 2026 CosmoCrew — a brand of <a href="https://luvita.tr/">Luvita Teknoloji Ltd. Şti.</a></footer>')
            code, out = run("--rules", RULES, "--root", tmp, "--format", "text")
            self.assertEqual(code, 0, out)
            self.assertIn("0 error(s), 1 warning(s)", out)  # sitemap warn only

    def test_bad_rules_exit_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "rules.json")
            with open(bad, "w", encoding="utf-8") as fh:
                json.dump({"rules": [{"id": "x", "kind": "banned", "pattern": "(", "paths": ["*"], "why": "y"}]}, fh)
            code, out = run("--rules", bad)
            self.assertEqual(code, 2)
            self.assertIn("bad regex", out)
            with open(bad, "w", encoding="utf-8") as fh:
                json.dump({"rules": [{"id": "x", "kind": "banned", "pattern": "a", "paths": ["*"]}]}, fh)
            code, out = run("--rules", bad)
            self.assertEqual(code, 2)
            self.assertIn("'why' is required", out)

    def test_string_valued_allow_or_exclude_is_a_configuration_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "rules.json")
            for field in ("allow", "exclude"):
                with open(bad, "w", encoding="utf-8") as fh:
                    json.dump({"rules": [{"id": "x", "kind": "banned", "pattern": "a", "paths": ["*"], "why": "y", field: "drafts/**"}]}, fh)
                code, out = run("--rules", bad)
                self.assertEqual(code, 2, out)
                self.assertIn(f"'{field}' must be a list", out)

    def test_required_rule_that_selects_no_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            rules = os.path.join(tmp, "rules.json")
            with open(rules, "w", encoding="utf-8") as fh:
                json.dump({"rules": [{"id": "footer", "kind": "required", "pattern": "x", "paths": ["/index.html"], "why": "y"}]}, fh)
            code, out = run("--rules", rules, "--root", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("[footer] required rule matched no file under /index.html", out)

    def test_ignore_prunes_the_real_directory_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "pages"))
            with open(os.path.join(tmp, "pages", "claim.html"), "w", encoding="utf-8") as fh:
                fh.write("banned-word")
            rules = os.path.join(tmp, "rules.json")
            with open(rules, "w", encoding="utf-8") as fh:
                json.dump({"ignore": ["pages/x"], "rules": [{"id": "w", "kind": "banned", "pattern": "banned-word", "paths": ["**/*.html"], "why": "y"}]}, fh)
            code, out = run("--rules", rules, "--root", tmp)
            self.assertEqual(code, 1, out)
            with open(rules, "w", encoding="utf-8") as fh:
                json.dump({"ignore": ["pages/**"], "rules": [{"id": "w", "kind": "banned", "pattern": "banned-word", "paths": ["**/*.html"], "why": "y"}]}, fh)
            code, out = run("--rules", rules, "--root", tmp)
            self.assertEqual(code, 0, out)

    def test_multiline_allow_keeps_line_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "a.md"), "w", encoding="utf-8") as fh:
                fh.write("legal name\nspans lines\nthen a banned word\n")
            rules = os.path.join(tmp, "rules.json")
            with open(rules, "w", encoding="utf-8") as fh:
                json.dump({"rules": [{"id": "w", "kind": "banned", "pattern": "banned", "paths": ["*.md"], "allow": ["legal name\nspans lines"], "why": "y"}]}, fh)
            code, out = run("--rules", rules, "--root", tmp)
            self.assertIn("a.md:3: error: [w]", out)

    def test_github_annotations_are_workspace_relative_and_escaped(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "site", "en"))
            with open(os.path.join(tmp, "site", "en", "index.html"), "w", encoding="utf-8") as fh:
                fh.write("<p>bad:thing</p>")
            rules = os.path.join(tmp, "rules.json")
            with open(rules, "w", encoding="utf-8") as fh:
                json.dump({"root": "site", "rules": [{"id": "w,x", "kind": "banned", "pattern": "bad:thing", "paths": ["**/*.html"], "why": "100% sure"}]}, fh)
            old = os.environ.get("GITHUB_WORKSPACE")
            os.environ["GITHUB_WORKSPACE"] = tmp
            try:
                code, out = run("--rules", rules, "--format", "github")
            finally:
                if old is None:
                    del os.environ["GITHUB_WORKSPACE"]
                else:
                    os.environ["GITHUB_WORKSPACE"] = old
            self.assertIn("::error file=site/en/index.html,line=1,title=brand-check w%2Cx::[w,x] banned: 'bad:thing' — 100%25 sure", out)

    def test_github_output_receives_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_file = os.path.join(tmp, "out.txt")
            os.environ["GITHUB_OUTPUT"] = out_file
            try:
                run("--rules", RULES, "--format", "text")
            finally:
                del os.environ["GITHUB_OUTPUT"]
            with open(out_file, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "errors=7\nwarnings=2\nrules=10\n")

    def test_missing_root_exit_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run("--rules", RULES, "--root", os.path.join(tmp, "dist"))
            self.assertEqual(code, 2)
            self.assertIn("build the site first", out)


if __name__ == "__main__":
    unittest.main()
