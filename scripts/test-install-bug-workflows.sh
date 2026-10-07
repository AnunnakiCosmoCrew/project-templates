#!/usr/bin/env bash
# Installs scripts/install-bug-workflows.sh into a temp dir and asserts the
# substituted values landed, placeholders are gone, and bad input is
# rejected. Run from anywhere; exits non-zero on the first failed assertion.
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
installer="$script_dir/install-bug-workflows.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

fail() { echo "FAIL: $1" >&2; exit 1; }

# --- happy path --------------------------------------------------------
"$installer" "$tmp" PEL bug >/dev/null

close_audit="$tmp/.github/workflows/bug-close-audit.yml"
needs_test="$tmp/.github/workflows/bug-needs-test.yml"

[ -f "$close_audit" ] || fail "bug-close-audit.yml not installed"
[ -f "$needs_test" ] || fail "bug-needs-test.yml not installed"

grep -q "PEL-" "$close_audit" || fail "issue-key prefix not substituted in bug-close-audit.yml"
grep -qF "'bug'" "$close_audit" || fail "bug label not substituted in bug-close-audit.yml if: condition"
grep -qF '"bug"' "$needs_test" || fail "bug label not substituted in bug-needs-test.yml"
grep -qF "no-test-required" "$needs_test" || fail "no-test-required escape label missing"

if grep -qF -e '{{ISSUE_KEY_PREFIX}}' -e '{{BUG_LABEL}}' "$close_audit" "$needs_test"; then
  fail "leftover {{ISSUE_KEY_PREFIX}} / {{BUG_LABEL}} placeholder after substitution"
fi

# Both files must still be valid YAML after substitution. Ruby (with its
# bundled YAML library) ships on both macOS and GitHub's ubuntu-latest
# runners, so this needs no extra install.
for f in "$close_audit" "$needs_test"; do
  ruby -ryaml -e 'YAML.load_file(ARGV[0])' "$f" \
    || fail "$f is not valid YAML after substitution"
done

# --- functional: the installed test-path globs actually match ------------
# Extract the real pathspec list from the installed file (not a hand-copied
# duplicate that could drift) and exercise it against a scratch git repo
# covering each ecosystem's top-level test convention. A plain pathspec
# needs a literal `/` before `test` for `**/test/**` to match a top-level
# test/ directory — exactly the bug three installs' auto-reviews caught.
pathspecs=()
while IFS= read -r spec; do
  pathspecs+=("$spec")
done < <(sed -n '/--numstat/,/| awk/p' "$needs_test" | grep -oE ":\(glob\)[^'\\]*")
[ "${#pathspecs[@]}" -gt 0 ] || fail "could not extract test-path globs from bug-needs-test.yml"

repo="$tmp/repo"
mkdir -p "$repo"
git -C "$repo" init -q -b main
git -C "$repo" config user.email test@example.com
git -C "$repo" config user.name test
echo x > "$repo/README.md"
git -C "$repo" -c commit.gpgsign=false add -A
git -C "$repo" -c commit.gpgsign=false commit -q -m base
git -C "$repo" switch -q -c work main

case_added() {   # $1 = relative path to add one line under
  git -C "$repo" reset -q --hard main
  mkdir -p "$repo/$(dirname "$1")"
  echo "line" >> "$repo/$1"
  git -C "$repo" add "$1"
  git -C "$repo" -c commit.gpgsign=false commit -q -m "add $1"
  git -C "$repo" diff main..HEAD --numstat -- "${pathspecs[@]}" | awk '{s+=$1} END{print s+0}'
}

[ "$(case_added test/helpers/fake_x.dart)" -gt 0 ] || fail "top-level test/ not matched by the installed globs"
[ "$(case_added tests/calendar/test_apple.py)" -gt 0 ] || fail "top-level tests/ not matched by the installed globs"
[ "$(case_added integration_test/app_test.dart)" -gt 0 ] || fail "top-level integration_test/ not matched by the installed globs"
[ "$(case_added src/test/java/x/FooTest.java)" -gt 0 ] || fail "nested src/test/java/ not matched by the installed globs"
[ "$(case_added lib/foo.dart)" -eq 0 ] || fail "non-test file incorrectly counted as a test line"

# --- idempotent re-run ---------------------------------------------------
"$installer" "$tmp" PEL bug >/dev/null
grep -q "PEL-" "$close_audit" || fail "re-run broke the substitution"

# --- rejects a bad issue-key prefix ---------------------------------------
if "$installer" "$tmp" "123-not-a-prefix" bug >/dev/null 2>&1; then
  fail "installer accepted an issue-key-prefix that doesn't start with a letter"
fi

# --- rejects a bug label with shell/YAML metacharacters -------------------
if "$installer" "$tmp" PEL 'bug"; rm -rf /' >/dev/null 2>&1; then
  fail "installer accepted a bug label containing a quote"
fi

echo "ok: install-bug-workflows.sh"
