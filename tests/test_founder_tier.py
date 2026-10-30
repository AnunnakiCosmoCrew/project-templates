"""The founder-tier classifier in workflows/claude-pr-review.yml (luvita-docs ADR 0007 §1, §2;
project-templates#52). Standard library only.

The script and its TIER_RULES block are read straight out of the workflow file, so the test
runs the one copy the repos take. `classify` is a pure function over a file list (REST
`pulls/N/files` items) and a PR body; `main` is driven against a fake API to check the
labels it writes and the fail-safe."""
import pathlib
import re
import textwrap
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = (ROOT / "workflows" / "claude-pr-review.yml").read_text(encoding="utf-8")


def _script():
    m = re.search(r"python3 - <<'PY'\n(.*?)\n[ ]*PY\n", WORKFLOW, re.S)
    assert m, "founder-tier script not found"
    return textwrap.dedent(m.group(1))


def _rules_text():
    m = re.search(r"\n( +)TIER_RULES: \|\n((?:\1[ ]+.*\n|\n)+)", WORKFLOW)
    assert m, "TIER_RULES block not found"
    return textwrap.dedent(m.group(2))


T = {"__name__": "founder_tier"}
exec(compile(_script(), "founder-tier", "exec"), T)
RULES_TEXT = _rules_text()
RULES = T["parse_rules"](RULES_TEXT, "TIER_RULES")
LINE = "Founder check: none"


def f(name, patch="@@ -1 +1 @@\n-a\n+b", status="modified", previous=None):
    item = {"filename": name, "status": status}
    if patch is not None:
        item["patch"] = patch
    if previous:
        item["previous_filename"] = previous
    return item


def classify(files, body=LINE, rules=RULES, **kw):
    return T["classify"](files, body, rules, **kw)


class PathTable(unittest.TestCase):
    """One case per row of the ADR 0007 §1 table, plus the tidying row."""

    def assertTier(self, name, tier, patch="@@ -1 +1 @@\n-a\n+b"):
        r = classify([f(name, patch)])
        self.assertIn(tier, r["tiers"], (name, r))
        self.assertIn("tier:" + tier, r["labels"])
        self.assertIn("needs-founder-review", r["labels"])

    def test_security(self):
        for name in [".github/workflows/ci.yml", ".github/CODEOWNERS", "CODEOWNERS", ".claude/settings.json",
                     "app/.claude/skills/x.md", "src/main/java/dev/x/auth/JwtFilter.java", "lib/services/oauth.dart",
                     "src/useAuth.ts", "backend/src/main/java/dev/x/security/Config.java", ".env.production",
                     "ios/Runner/Runner.entitlements", "firestore.rules"]:
            with self.subTest(name):
                self.assertTier(name, "security")

    def test_dependency_files_are_security(self):
        for name in ["pom.xml", "backend/build.gradle.kts", "pubspec.yaml", "app/pubspec.lock", "package.json",
                     "web/package-lock.json", "yarn.lock", "pnpm-lock.yaml", "gradle/libs.versions.toml",
                     "requirements-dev.txt", "Podfile.lock", "Cargo.lock", "go.sum"]:
            with self.subTest(name):
                self.assertTier(name, "security")

    def test_irreversible(self):
        for name in ["src/main/resources/db/migration/V12__add_users.sql", "migrations/0001_init.py",
                     "prisma/schema.prisma", "infra/main.tf", "deploy/cloudrun.yaml", "Dockerfile",
                     "cloudbuild.yaml", "wrangler.toml", "firebase.json", "public/_redirects", "ios/fastlane/Fastfile"]:
            with self.subTest(name):
                self.assertTier(name, "irreversible")

    def test_money(self):
        for name in ["src/main/java/dev/x/billing/Invoice.java", "lib/paywall_screen.dart", "src/PaymentService.kt",
                     "lib/iap/store.dart", "infra/cloud_run.tf"]:
            with self.subTest(name):
                self.assertTier(name, "money")

    def test_scheduled_workflow_and_runner_are_money(self):
        cron = "@@ -3,0 +4,2 @@\n+  schedule:\n+    - cron: '0 8 * * *'"
        runner = "@@ -9 +9 @@\n-    runs-on: ubuntu-latest\n+    runs-on: macos-15"
        self.assertTier(".github/workflows/nightly.yml", "money", cron)
        self.assertTier(".github/workflows/ios.yml", "money", runner)
        plain = classify([f(".github/workflows/ci.yml", "@@ -20 +20 @@\n-      run: make a\n+      run: make b")])
        self.assertEqual(plain["tiers"], ["security"])

    def test_workflow_with_unreadable_diff_is_money(self):
        r = classify([f(".github/workflows/big.yml", patch=None)])
        self.assertEqual(r["tiers"], ["security", "money"])

    def test_public(self):
        for name in ["src/content/blog/launch.md", "src/pages/about.mdx", "lib/l10n/app_tr.arb",
                     "src/locales/en.json", "ios/fastlane/metadata/en-US/description.txt", "public/privacy.html",
                     "src/pages/terms.astro", "LICENSE", "public/favicon.ico", "assets/brand/logo.svg",
                     "Runner/Localizable.xcstrings"]:
            with self.subTest(name):
                self.assertTier(name, "public")

    def test_tidying(self):
        files = [f("src/main/java/dev/x/service/FooService.java"), f("README.md"), f("docs/notes.md"),
                 f("lib/widgets/old.dart", status="renamed", previous="lib/widgets/older.dart")]
        r = classify(files)
        self.assertEqual(r["tiers"], ["none"])
        self.assertEqual(r["labels"], ["tier:none"])
        self.assertEqual(r["feature"], [])

    def test_no_files_is_tidying(self):
        self.assertEqual(classify([])["labels"], ["tier:none"])

    def test_near_misses_stay_none(self):
        """Names that look like a rule but are not: the kill criterion is a classifier that
        labels half the PRs founder-tier, so these must not trip it."""
        for name in ["lib/screens/logout_button.dart", "src/Author.java", "src/hooks/useTimer.ts",
                     "lib/models/pomodoro_session.dart", "docs/notes/tokens.md", "src/sessionTimer.ts"]:
            with self.subTest(name):
                self.assertEqual(classify([f(name)])["tiers"], ["none"])

    def test_renamed_file_is_checked_under_both_names(self):
        r = classify([f("docs/old-workflow.yml", status="renamed", previous=".github/workflows/old.yml")])
        self.assertIn("security", r["tiers"])

    def test_truncated_file_list_is_security(self):
        r = classify([f("README.md")], truncated=True)
        self.assertIn("security", r["tiers"])
        self.assertIn("needs-founder-review", r["labels"])


class FounderCheckLine(unittest.TestCase):
    def test_missing_line_is_product(self):
        r = classify([f("README.md")], body="Closes #3\n\nSmall docs fix.")
        self.assertEqual(r["tiers"], ["product"])
        self.assertIn("needs-founder-review", r["labels"])
        r = classify([f("README.md")], body=None)
        self.assertEqual(r["tiers"], ["product"])

    def test_line_can_raise(self):
        r = classify([f("README.md")], body="Founder check: public: the new tagline on the home page")
        self.assertEqual(r["labels"], ["tier:public", "needs-founder-review"])

    def test_line_can_never_lower(self):
        r = classify([f(".github/workflows/ci.yml")], body="Founder check: none")
        self.assertEqual(r["tiers"], ["security"])

    def test_both_kept_when_they_differ(self):
        r = classify([f("db/migrations/V3__x.sql")], body="Founder check: money: new paid tier")
        self.assertEqual(r["tiers"], ["irreversible", "money"])

    def test_formats(self):
        for body, want in [("**Founder check:** security: review workflow logic", ["security"]),
                           ("- Founder check: `money`: runner minutes", ["money"]),
                           ("> founder check: IRREVERSIBLE: prod deploy", ["irreversible"]),
                           ("Founder check: none (docs only)", ["none"]),
                           ("Founder check: maybe", ["product"]),
                           ("Founder check: <tier>: <what to verify>", ["product"]),
                           ("Every PR carries `Founder check: none`.", ["product"])]:
            with self.subTest(body):
                self.assertEqual(classify([], body=body)["tiers"], want)


class TidyingTest(unittest.TestCase):
    """ADR 0007 §2: the script, not the agent, decides what is tidying."""

    def test_assertion_added_changed_or_removed_is_feature(self):
        for patch in ["@@ -0,0 +1 @@\n+    assertEquals(2, add(1, 1));",
                      "@@ -4 +4 @@\n-    expect(total, 3);\n+    expect(total, 4);",
                      "@@ -4 +3,0 @@\n-        XCTAssertEqual(a, b)",
                      "@@ -1 +1 @@\n-  assert result == 1\n+  assert result == 2",
                      "@@ -1 +1 @@\n+    expect(screen.getByText('Hi')).toBeVisible();",
                      "@@ -1 +1 @@\n+    verify(repo).save(any());"]:
            with self.subTest(patch):
                r = classify([f("src/test/java/dev/x/AddTest.java", patch)])
                self.assertEqual(r["tiers"], ["none"])
                self.assertIn("needs-founder-review", r["labels"])
                self.assertTrue(any("assertion" in x for x in r["feature"]))

    def test_test_file_without_assertion_change_is_tidying(self):
        patch = "@@ -1,2 +1,2 @@\n-import dev.x.old.Foo;\n+import dev.x.service.Foo;"
        r = classify([f("app/test/widgets/foo_test.dart", patch), f("lib/service/foo.dart")])
        self.assertEqual(r["labels"], ["tier:none"])

    def test_assertion_in_source_file_does_not_count(self):
        r = classify([f("lib/service/foo.dart", "@@ -1 +1 @@\n+  assert(x != null);")])
        self.assertEqual(r["labels"], ["tier:none"])

    def test_unreadable_test_diff_is_feature(self):
        r = classify([f("src/test/java/dev/x/BigTest.java", patch=None)])
        self.assertIn("needs-founder-review", r["labels"])
        big = dict(f("src/test/java/dev/x/BigTest.java", patch=None), changes=4000)
        self.assertIn("needs-founder-review", classify([big])["labels"])

    def test_pure_rename_of_a_test_file_is_tidying(self):
        moved = dict(f("src/test/java/dev/x/new/FooTest.java", patch=None, status="renamed",
                       previous="src/test/java/dev/x/FooTest.java"), changes=0)
        self.assertEqual(classify([moved])["labels"], ["tier:none"])

    def test_summary_neutralises_file_names(self):
        r = classify([f(".github/workflows/a\n::error::x`y.yml")])
        self.assertIn("security", r["tiers"])          # a newline in the name does not dodge `**`
        text = T["summary"](r, [])
        self.assertIn("?::error::x?y.yml", text)
        self.assertNotIn("\n::error::", text)
        self.assertNotIn("x`", text)

    def test_test_file_conventions(self):
        a = "@@ -0,0 +1 @@\n+  expect(x).toBe(1)"
        for name in ["test/foo_test.dart", "web/src/__tests__/a.ts", "src/a.test.ts", "src/a.spec.ts",
                     "tests/test_a.py", "AppTests/LoginTests.swift", "app/integration_test/flow_test.dart"]:
            with self.subTest(name):
                self.assertIn("needs-founder-review", classify([f(name, a)])["labels"])

    def test_config_change_is_feature_without_a_tier(self):
        for name in ["src/main/resources/application.yml", "web/vite.config.ts", "tsconfig.json",
                     "ios/Runner/Info.plist", "app/analysis_options.yaml", "gradle.properties"]:
            with self.subTest(name):
                r = classify([f(name)])
                self.assertEqual(r["tiers"], ["none"], name)
                self.assertEqual(r["labels"], ["tier:none", "needs-founder-review"])


class Rules(unittest.TestCase):
    def test_every_key_is_present_and_compiles(self):
        self.assertEqual(set(RULES), set(T["KNOWN_KEYS"]))
        for k in T["KNOWN_KEYS"]:
            self.assertTrue(RULES[k], k)
        T["compile_rules"](RULES)

    def test_extension_adds_and_never_removes(self):
        extra = T["parse_rules"]("security:\n  - 'workflows/**'\npublic:\n  - src/pages/**\n", "ext")
        merged = T["merge"](RULES, extra)
        for k in RULES:
            self.assertTrue(set(RULES[k]) <= set(merged[k]), k)
        self.assertIn("workflows/**", merged["security"])
        self.assertEqual(classify([f("workflows/ci.yml")], rules=merged)["tiers"], ["security"])
        self.assertEqual(classify([f("src/pages/index.astro")], rules=merged)["tiers"], ["public"])
        self.assertEqual(classify([f("src/pages/index.astro")])["tiers"], ["none"])

    def test_bad_extension_is_an_error(self):
        for text in ["secrity:\n  - x\n", "security:\n  x\n", "  - orphan\n", "security: [a, b]\n"]:
            with self.subTest(text), self.assertRaises(ValueError):
                T["parse_rules"](text, "ext")

    def test_this_repos_extension_parses(self):
        ext = ROOT / ".github" / "founder-tier.yml"
        merged = T["merge"](RULES, T["parse_rules"](ext.read_text(encoding="utf-8"), str(ext)))
        T["compile_rules"](merged)
        r = classify([f("workflows/claude-pr-review.yml")], rules=merged)
        self.assertIn("security", r["tiers"])

    def test_glob(self):
        rx = lambda p: T["glob_re"](p)
        cases = [(".github/**", ".github/workflows/a.yml", True), (".github/**", "x/.github/a", False),
                 ("**/migrations/**", "migrations/1.sql", True), ("**/migrations/**", "a/b/migrations/c/1.sql", True),
                 ("**/migrations/**", "a/migrationsx/1.sql", False), ("pom.xml", "svc/pom.xml", True),
                 ("src/content/**", "web/src/content/a.md", False), ("src/**/*.md", "src/a.md", True),
                 ("src/**/*.md", "src/x/y/a.md", True), ("*.test.*", "a/b.test.ts", True), ("*Test.java", "a/FooTest.java", True)]
        for pat, path, want in cases:
            with self.subTest((pat, path)):
                self.assertEqual(T["matches"]([rx(pat)], path), want)


class FakeApi:
    def __init__(self, files, body=LINE, labels=(), fail=None, ext=None, changed=None):
        self.files, self.body, self.labels, self.fail, self.ext = files, body, list(labels), fail, ext
        self.changed = len(files) if changed is None else changed
        self.calls = []

    def call(self, method, path, data=None, accept=None):
        import json
        self.calls.append((method, path, data))
        if self.fail and self.fail in path and method == "GET":
            return 500, b"boom"
        if method == "GET" and path.endswith("/pulls/7"):
            return 200, json.dumps({"body": self.body, "labels": [{"name": n} for n in self.labels],
                                    "base": {"sha": "abc"}, "changed_files": self.changed}).encode()
        if method == "GET" and "/contents/.github/founder-tier.yml?ref=abc" in path:
            return (200, self.ext.encode()) if self.ext else (404, b"")
        if method == "GET" and "/pulls/7/files" in path:
            page = int(re.search(r"[?&]page=(\d+)", path).group(1))
            return 200, json.dumps(self.files[(page - 1) * 100: page * 100]).encode()
        if method == "POST" and path.endswith("/labels") and "/issues/" not in path:
            return 422, b""
        if method == "POST" and path.endswith("/issues/7/labels"):
            self.labels += data["labels"]
            return 200, b"[]"
        if method == "DELETE":
            name = path.rsplit("/", 1)[-1].replace("%3A", ":")
            self.labels.remove(name)
            return 200, b""
        return 404, b""

    def json(self, method, path, data=None):
        return T["Api"].json(self, method, path, data)


def env(**kw):
    return dict({"REPO": "AnunnakiCosmoCrew/x", "PR": "7", "TIER_RULES": RULES_TEXT}, **kw)


_main = T["main"]


def run_main(api, e):
    """main() prints its summary and ::error:: lines; keep the test output readable."""
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):
        return _main(api, e)


class Main(unittest.TestCase):
    def test_sets_labels_and_removes_stale_ones(self):
        api = FakeApi([f(".github/workflows/ci.yml")], labels=["tier:none", "claude-review", "tier:public"])
        self.assertEqual(run_main(api, env()), 0)
        self.assertEqual(sorted(api.labels), ["claude-review", "needs-founder-review", "tier:security"])

    def test_tidying_removes_needs_founder_review(self):
        api = FakeApi([f("README.md")], labels=["needs-founder-review", "tier:security"])
        self.assertEqual(run_main(api, env()), 0)
        self.assertEqual(api.labels, ["tier:none"])

    def test_reads_all_pages(self):
        files = [f(f"docs/{i}.md") for i in range(250)] + [f("pom.xml")]
        api = FakeApi(files)
        run_main(api, env())
        self.assertIn("tier:security", api.labels)

    def test_extension_is_read_from_the_base_commit(self):
        api = FakeApi([f("src/pages/index.astro")], ext="public:\n  - src/pages/**\n")
        run_main(api, env())
        self.assertIn("tier:public", api.labels)
        self.assertTrue(any("ref=abc" in p for _, p, _ in api.calls))

    def test_fail_safe_on_api_error(self):
        api = FakeApi([f("README.md")], labels=["tier:none"], fail="/files")
        self.assertEqual(run_main(api, env()), 1)
        self.assertIn("needs-founder-review", api.labels)
        self.assertIn("tier:security", api.labels)

    def test_fail_safe_on_bad_extension(self):
        api = FakeApi([f("README.md")], ext="nonsense: here\n")
        self.assertEqual(run_main(api, env()), 1)
        self.assertIn("tier:security", api.labels)

    def test_fail_safe_on_bad_pr_number(self):
        api = FakeApi([f("README.md")])
        self.assertEqual(run_main(api, env(PR="7; rm -rf /")), 1)

    def test_summary_written(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile("r", suffix=".md", delete=False) as fh:
            path = fh.name
        try:
            run_main(FakeApi([f("pom.xml")]), env(GITHUB_STEP_SUMMARY=path))
            text = pathlib.Path(path).read_text(encoding="utf-8")
            self.assertIn("`tier:security`", text)
            self.assertIn("`pom.xml`", text)
        finally:
            os.unlink(path)


class WorkflowShape(unittest.TestCase):
    def test_no_checkout_and_no_expressions_in_the_script(self):
        job = WORKFLOW.split("\n  founder-tier:\n", 1)[1].split("\n  review:\n", 1)[0]
        self.assertNotIn("actions/checkout", job)
        self.assertNotIn("${{", _script())
        self.assertIn("pull_request_target:", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
