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

# --- functional: the installed issue-reference pattern ----------------------
# Extract the real `pattern=` line from the installed file and run it through
# the same `git log --perl-regexp --grep` call the workflow uses, against
# commit messages covering true positives and the false positives raised on
# handlebars-web#133 (no left boundary; any passing mention counted).
pattern_line="$(grep -E '^[[:space:]]+(ref|pattern)="' "$close_audit" | sed 's/^[[:space:]]*//')"
[ "$(printf '%s\n' "$pattern_line" | wc -l | tr -d ' ')" -eq 2 ] || fail "need exactly one ref= and one pattern= line in bug-close-audit.yml"

audit_repo="$tmp/audit-repo"
mkdir -p "$audit_repo"
git -C "$audit_repo" init -q -b main
git -C "$audit_repo" config user.email test@example.com
git -C "$audit_repo" config user.name test
n=0
commit_msg() {   # $1 = full commit message
  n=$((n + 1))
  git -C "$audit_repo" -c commit.gpgsign=false commit -q --allow-empty -m "$1"
}
matches() {      # $1 = issue number, $2 = commit message; prints match count
  git -C "$audit_repo" reset -q --hard "$base"
  commit_msg "$2"
  ( ISSUE="$1"; REPO="${3:-AnunnakiCosmoCrew/Pelerin}"; eval "$pattern_line"
    git -C "$audit_repo" log --perl-regexp --regexp-ignore-case --grep="$pattern" \
      --pretty=tformat:%H "$base"..HEAD | wc -l | tr -d ' ' )
}
commit_msg base
base="$(git -C "$audit_repo" rev-parse HEAD)"

# true positives
[ "$(matches 12 'PEL-12: fix login')" -eq 1 ]            || fail "subject prefix PEL-12 not matched"
[ "$(matches 12 '[PEL-12] fix login')" -eq 1 ]           || fail "bracketed [PEL-12] not matched"
[ "$(matches 12 $'Fix login\n\nCloses #12')" -eq 1 ]     || fail "Closes #12 not matched"
[ "$(matches 12 'Fixes #12')" -eq 1 ]                    || fail "Fixes #12 not matched"
[ "$(matches 12 'resolved: PEL-12')" -eq 1 ]             || fail "resolved: PEL-12 not matched"
[ "$(matches 12 $'Tidy\n\nPEL-12 follow-up')" -eq 1 ]    || fail "body line starting with PEL-12 not matched"
[ "$(matches 12 'fix(auth): PEL-12 stop token reuse')" -eq 1 ] || fail "conventional-commit prefix before PEL-12 not matched"
[ "$(matches 12 'feat: [PEL-12] add export')" -eq 1 ]    || fail "feat: [PEL-12] not matched"
[ "$(matches 12 'Fixes #11, #12')" -eq 1 ]               || fail "Fixes #11, #12 did not credit #12"
[ "$(matches 12 'Closes #11 and #12')" -eq 1 ]           || fail "Closes #11 and #12 did not credit #12"
[ "$(matches 12 'Fixes PEL-3, PEL-7 & PEL-12')" -eq 1 ]  || fail "keyed list did not credit PEL-12"
[ "$(matches 12 'fix(auth): handle token reuse (PEL-12)')" -eq 1 ] || fail "key closing the subject not matched"
[ "$(matches 12 'fix: handle token reuse (PEL-12) (#45)')" -eq 1 ]      || fail "key before a squash PR number not matched"
[ "$(matches 12 'Fixes #11, and #12')" -eq 1 ]           || fail "Fixes #11, and #12 did not credit #12"
[ "$(matches 12 'Closes #11, #13 and #12')" -eq 1 ]      || fail "three-item list did not credit #12"
[ "$(matches 12 'Fixes #11 #12')" -eq 1 ]                || fail "space-separated list did not credit #12"
[ "$(matches 12 'Closes AnunnakiCosmoCrew/Pelerin#12')" -eq 1 ] || fail "owner/repo#12 not matched"
[ "$(matches 12 'Closes https://github.com/AnunnakiCosmoCrew/Pelerin/issues/12')" -eq 1 ] || fail "issue URL not matched"
# false positives
[ "$(matches 12 'see the discussion in (PEL-12)')" -eq 0 ] || fail "bare (PEL-12) mention wrongly credited"
[ "$(matches 12 'follow-up to [PEL-12]')" -eq 0 ]        || fail "bare [PEL-12] mention wrongly credited"
[ "$(matches 12 'Closes o/aXb#12' o/a.b)" -eq 0 ]        || fail "'.' in REPO not escaped"
[ "$(matches 12 'Closes o/a.b#12' o/a.b)" -eq 1 ]        || fail "dotted REPO form not matched"
[ "$(matches 12 'Closes AnunnakiCosmoCrew/Other#12')" -eq 0 ] || fail "another repo's #12 wrongly credited"
[ "$(matches 12 'Closes https://github.com/AnunnakiCosmoCrew/Other/issues/12')" -eq 0 ] || fail "another repo's issue URL wrongly credited"
[ "$(matches 12 'Fixes #11 but not unrelated #12')" -eq 0 ] || fail "keyword followed by prose wrongly credited #12"
[ "$(matches 12 'handle x (PEL-123)')" -eq 0 ]           || fail "(PEL-123) wrongly matched PEL-12"
[ "$(matches 12 'Fixes #11, #123')" -eq 0 ]              || fail "#123 in a list wrongly credited #12"
[ "$(matches 12 'chore: bump deps, see PEL-12')" -eq 0 ] || fail "conventional prefix + passing mention wrongly counted"
[ "$(matches 12 'WPEL-12: fix login')" -eq 0 ]           || fail "WPEL-12 wrongly matched PEL-12"
[ "$(matches 12 'Fixes WPEL-12')" -eq 0 ]                || fail "Fixes WPEL-12 wrongly matched PEL-12"
[ "$(matches 12 'Fixes foo#12')" -eq 0 ]                 || fail "Fixes foo#12 wrongly matched #12"
[ "$(matches 12 'Update docs, see #12')" -eq 0 ]         || fail "passing mention of #12 wrongly counted as a fix"
[ "$(matches 12 'Related to PEL-12')" -eq 0 ]            || fail "passing mention of PEL-12 wrongly counted as a fix"
[ "$(matches 12 'Closes #123')" -eq 0 ]                  || fail "#123 wrongly matched #12"
[ "$(matches 12 'PEL-123: other work')" -eq 0 ]          || fail "PEL-123 wrongly matched PEL-12"
[ "$(matches 12 'prefixes #12 in output')" -eq 0 ]       || fail "'prefixes #12' wrongly counted as a fix keyword"

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
