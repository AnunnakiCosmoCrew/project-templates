#!/usr/bin/env bash
# Installs the one generic machine-global asset kept in this public repo: the
# /resolve-copilot command. The worktree skill, the prune scripts, the
# SessionStart auto-prune hook and the PreToolUse guards moved to the private
# `emirers` repo on 2026-10-06 (luvita-docs ADR 0003); install those with
#   cd ~/Projects/emirers && ./install.sh
# Idempotent.
set -euo pipefail

src="$(cd "$(dirname "$0")/../global" && pwd)"
claude="$HOME/.claude"

mkdir -p "$claude/commands"
cp "$src/commands/resolve-copilot.md" "$claude/commands/resolve-copilot.md"
echo "Installed: ~/.claude/commands/resolve-copilot.md"

if [ ! -e "$claude/skills/worktree" ] || [ ! -e "$claude/scripts/prune-current-worktrees.sh" ]; then
  echo "note: the worktree skill / prune hook are not installed; run: cd ~/Projects/emirers && ./install.sh"
fi
