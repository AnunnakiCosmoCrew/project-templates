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
