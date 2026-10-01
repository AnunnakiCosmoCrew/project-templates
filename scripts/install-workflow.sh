#!/usr/bin/env bash
# Scaffold the per-project workflow skills (issue-start, pr-open) into a repo,
# substituting the template placeholders.
#
# The worktree skill is GLOBAL (~/.claude/skills/worktree) and is NOT copied per
# repo — it's shared by every project. The auto-prune SessionStart hook is also
# global. Run ./scripts/install-global-workflow.sh once per machine to install
# those (see README "One-time global setup").
#
# Usage:
#   install-workflow.sh <repo-dir> \
#     --name "WordPower" --prefix WP --branch-prefix feature/wp \
#     --worktree-prefix wp --board 11 --app-repo WordPower-app [--owner AnunnakiCosmoCrew]
set -euo pipefail

repo="${1:?usage: install-workflow.sh <repo-dir> --name N --prefix P --branch-prefix BP --worktree-prefix WP --board B --app-repo R [--owner O]}"
shift

owner="AnunnakiCosmoCrew"
name="" prefix="" branch_prefix="" worktree_prefix="" board="" app_repo=""
while [ $# -gt 0 ]; do
  case "$1" in
    --name)            name="$2";            shift 2;;
    --prefix)          prefix="$2";          shift 2;;
    --branch-prefix)   branch_prefix="$2";   shift 2;;
    --worktree-prefix) worktree_prefix="$2"; shift 2;;
    --board)           board="$2";           shift 2;;
    --app-repo)        app_repo="$2";        shift 2;;
    --owner)           owner="$2";           shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

missing=""
for v in name prefix branch_prefix worktree_prefix board app_repo; do
  [ -n "${!v}" ] || missing="$missing --${v//_/-}"
done
[ -z "$missing" ] || { echo "missing required:$missing" >&2; exit 2; }
[ -d "$repo" ] || { echo "no such repo dir: $repo" >&2; exit 2; }

script_dir="$(cd "$(dirname "$0")" && pwd)"
tpl_dir="$script_dir/../skill-templates"
dest="$repo/.claude/skills"
mkdir -p "$dest/issue-start" "$dest/pr-open"

subst() {
  sed -e '/<!-- TEMPLATE NOTE/,/-->/d' \
      -e "s|{{PROJECT_NAME}}|$name|g" \
      -e "s|{{ISSUE_PREFIX}}|$prefix|g" \
      -e "s|{{BRANCH_PREFIX}}|$branch_prefix|g" \
      -e "s|{{WORKTREE_PREFIX}}|$worktree_prefix|g" \
      -e "s|{{PROJECT_BOARD_NUMBER}}|$board|g" \
      -e "s|{{APP_REPO}}|$app_repo|g" \
      -e "s|{{REPO_OWNER}}|$owner|g"
}

subst < "$tpl_dir/issue-start/SKILL.md" > "$dest/issue-start/SKILL.md"
subst < "$tpl_dir/pr-open/SKILL.md"     > "$dest/pr-open/SKILL.md"

echo "Installed workflow skills into $dest/{issue-start,pr-open}/"
echo
echo "Next steps:"
echo "  1. Fill the <!-- FILL --> required-status-checks list in pr-open/SKILL.md."
echo "  2. Make sure the global worktree skill + prune hook are installed (one-time):"
echo "       $script_dir/install-global-workflow.sh"
echo "  3. Add the 'Workflows' + 'Agent Workflow' sections to this repo's CLAUDE.md"
echo "     (copy from project-templates/CLAUDE.template.md)."
