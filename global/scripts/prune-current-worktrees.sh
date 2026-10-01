#!/usr/bin/env bash
# SessionStart wrapper: prune merged worktrees for whatever project the session
# opened in. Reads the SessionStart hook's JSON payload on stdin, extracts `.cwd`,
# and delegates to prune-worktrees.sh. This replaces a hardcoded list of repo
# paths — every repo you open self-cleans, with zero per-project wiring.
#
# Safe anywhere: prune-worktrees.sh no-ops on non-git directories, leaves dirty
# trees and claude/* agent-harness branches alone.
set -euo pipefail

payload="$(cat)"

cwd=""
if command -v jq >/dev/null 2>&1; then
  cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null || true)"
elif command -v python3 >/dev/null 2>&1; then
  cwd="$(printf '%s' "$payload" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("cwd",""))' 2>/dev/null || true)"
fi

# Fallback: if stdin had no usable cwd, use the process working directory.
[ -z "${cwd:-}" ] && cwd="$(pwd -P)"
[ -z "${cwd:-}" ] && exit 0

exec "$HOME/.claude/scripts/prune-worktrees.sh" "$cwd"
