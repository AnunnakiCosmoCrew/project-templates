#!/usr/bin/env bash
# Remove git worktrees whose branch is gone from origin AND working tree is clean.
# Usage: prune-worktrees.sh <repo-path> [--dry-run]

set -euo pipefail

repo="${1:?usage: prune-worktrees.sh <repo-path> [--dry-run]}"
dry="${2:-}"
{ [ -d "$repo/.git" ] || [ -f "$repo/.git" ]; } || exit 0

# Capture caller's cwd BEFORE cd, so we never remove the worktree we're running in
self="$(pwd -P)"

cd "$repo"

git fetch --prune origin --quiet 2>/dev/null || true

remote_branches=$(git ls-remote --heads origin 2>/dev/null \
  | awk '{sub("refs/heads/","",$2); print $2}' | sort -u)

git worktree list --porcelain | awk '
  /^worktree / { wt=$2 }
  /^branch / { sub("refs/heads/","",$2); print wt "\t" $2 }
' | while IFS=$'\t' read -r path branch; do
  [ "$path" = "$repo" ] && continue
  [ "$path" = "$self" ] && continue

  # Leave agent-harness branches alone — they belong to (possibly other) live sessions
  case "$branch" in claude/*) continue ;; esac

  if printf '%s\n' "$remote_branches" | grep -qx "$branch"; then
    continue
  fi

  if [ -n "$(git -C "$path" status --porcelain 2>/dev/null)" ]; then
    echo "skip (dirty): $path"
    continue
  fi

  if [ "$dry" = "--dry-run" ]; then
    echo "would remove: $path  (branch=$branch)"
  else
    echo "removing:     $path  (branch=$branch)"
    git worktree unlock "$path" 2>/dev/null || true
    git worktree remove --force "$path" 2>/dev/null \
      || rm -rf "$path"
    git branch -D "$branch" 2>/dev/null || true
  fi
done

[ "$dry" = "--dry-run" ] || git worktree prune
