#!/usr/bin/env bash
# One-time-per-machine setup for the shared git workflow:
#   - installs the global `worktree` skill into ~/.claude/skills/
#   - installs the prune scripts into ~/.claude/scripts/
#   - wires the universal SessionStart auto-prune hook into ~/.claude/settings.json
#
# Idempotent: re-running refreshes the skill + scripts and leaves the hook alone
# if it's already wired.
set -euo pipefail

src="$(cd "$(dirname "$0")/../global" && pwd)"
claude="$HOME/.claude"
settings="$claude/settings.json"

mkdir -p "$claude/skills/worktree" "$claude/scripts"
cp "$src/skills/worktree/SKILL.md"            "$claude/skills/worktree/SKILL.md"
cp "$src/scripts/prune-worktrees.sh"          "$claude/scripts/prune-worktrees.sh"
cp "$src/scripts/prune-current-worktrees.sh"  "$claude/scripts/prune-current-worktrees.sh"
chmod +x "$claude/scripts/prune-worktrees.sh" "$claude/scripts/prune-current-worktrees.sh"
echo "Installed: ~/.claude/skills/worktree + ~/.claude/scripts/prune-*.sh"

if grep -q "prune-current-worktrees.sh" "$settings" 2>/dev/null; then
  echo "SessionStart auto-prune hook already wired — leaving as-is."
  exit 0
fi

if command -v jq >/dev/null 2>&1 && [ -f "$settings" ]; then
  tmp="$(mktemp)"
  jq '.hooks.SessionStart = ((.hooks.SessionStart // []) + [
        {"matcher":"","hooks":[{"type":"command","command":"$HOME/.claude/scripts/prune-current-worktrees.sh","async":true}]}
      ])' "$settings" > "$tmp" && mv "$tmp" "$settings"
  echo "Wired universal auto-prune hook into $settings (via jq)."
else
  echo
  echo "ACTION NEEDED: add this to the top-level \"hooks\" object in $settings:"
  cat <<'JSON'
  "SessionStart": [
    { "matcher": "", "hooks": [
      { "type": "command", "command": "$HOME/.claude/scripts/prune-current-worktrees.sh", "async": true }
    ] }
  ]
JSON
fi
