#!/usr/bin/env bash
# Copy vendored and shared skills from this repo's skills/ into a repo's
# .claude/skills/. Idempotent: a skill whose installed copy is already identical
# is left untouched (and says so); an older copy is replaced, stale files removed.
#
# Usage:
#   install-skills.sh <repo-dir> <skill>...
#
# Skills available: every directory under skills/ here (frontend-design,
# preview-check). An unknown skill name exits non-zero before anything is copied.
set -euo pipefail

usage='usage: install-skills.sh <repo-dir> <skill>...'
repo="${1:?$usage}"
shift
[ "$#" -ge 1 ] || { echo "$usage" >&2; exit 2; }
[ -d "$repo" ] || { echo "no such repo dir: $repo" >&2; exit 2; }

src_root="$(cd "$(dirname "$0")/../skills" && pwd)"

for skill in "$@"; do
  case "$skill" in
    */* | .* | "") echo "unknown skill: $skill" >&2; exit 1 ;;
  esac
  [ -d "$src_root/$skill" ] || { echo "unknown skill: $skill (have: $(ls "$src_root" | tr '\n' ' '))" >&2; exit 1; }
done

for skill in "$@"; do
  src="$src_root/$skill"
  dest="$repo/.claude/skills/$skill"
  if [ -d "$dest" ] && diff -r "$src" "$dest" >/dev/null 2>&1; then
    echo "unchanged: $dest"
    continue
  fi
  mkdir -p "$dest"
  rsync -a --delete "$src/" "$dest/"
  echo "installed: $dest"
done
