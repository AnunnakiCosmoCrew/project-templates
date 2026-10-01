#!/usr/bin/env bash
# SessionStart wrapper: prune merged worktrees for the project the session
# opened in. Bounded, non-blocking stdin read; delegates in the background.
# Hard rule: this script must NEVER block or delay session start.
set -euo pipefail

payload=""
if [ ! -t 0 ]; then
  while IFS= read -r -t 2 line || [ -n "${line:-}" ]; do
    payload+="${line}"$'\n'
    line=""
  done || true
fi

cwd=""
if [ -n "$payload" ]; then
  if command -v jq >/dev/null 2>&1; then
    cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null || true)"
  elif command -v python3 >/dev/null 2>&1; then
    cwd="$(printf '%s' "$payload" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("cwd",""))' 2>/dev/null || true)"
  fi
fi
[ -z "${cwd:-}" ] && cwd="$(pwd -P)"
[ -z "${cwd:-}" ] && exit 0

nohup "$HOME/.claude/scripts/prune-worktrees.sh" "$cwd" >/dev/null 2>&1 &
exit 0
