#!/usr/bin/env bash
# Checks install-skills.sh: installs, is a no-op the second time, repairs drift,
# and refuses an unknown skill.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

"$here/install-skills.sh" "$tmp" frontend-design preview-check >/dev/null
before="$(cd "$tmp" && find . -type f -exec shasum {} + | sort | shasum)"
out="$("$here/install-skills.sh" "$tmp" frontend-design preview-check)"
after="$(cd "$tmp" && find . -type f -exec shasum {} + | sort | shasum)"
[ "$before" = "$after" ] || { echo "FAIL: second run changed files" >&2; exit 1; }
[ "$(printf '%s\n' "$out" | grep -c '^unchanged:')" = 2 ] || { echo "FAIL: second run not a no-op: $out" >&2; exit 1; }

echo drift >> "$tmp/.claude/skills/preview-check/SKILL.md"
touch "$tmp/.claude/skills/preview-check/stale.txt"
"$here/install-skills.sh" "$tmp" preview-check >/dev/null
diff -r "$here/../skills/preview-check" "$tmp/.claude/skills/preview-check" >/dev/null \
  || { echo "FAIL: drift not repaired" >&2; exit 1; }

if "$here/install-skills.sh" "$tmp" no-such-skill 2>/dev/null; then
  echo "FAIL: unknown skill accepted" >&2; exit 1
fi
echo "ok"
