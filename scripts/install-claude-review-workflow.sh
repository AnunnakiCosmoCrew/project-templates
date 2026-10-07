#!/usr/bin/env bash
# Install the standard "Claude PR review" workflow into a repo. Idempotent:
# copies workflows/claude-pr-review.yml to <repo>/.github/workflows/claude-review.yml.
#
# Usage: install-claude-review-workflow.sh <repo-dir>
#
# The installed workflow is OFF (and free) until the repo opts in:
#   claude setup-token                                   # prints a Max OAuth token
#   gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo <owner>/<repo>
#   gh variable set CLAUDE_REVIEW_ENABLED --body true --repo <owner>/<repo>
#   gh label create claude-review --color 5319e7 --repo <owner>/<repo>   # backfill label
set -euo pipefail
usage='usage: install-claude-review-workflow.sh <repo-dir>'
repo="${1:?$usage}"
[ -d "$repo" ] || { echo "no such repo dir: $repo" >&2; exit 2; }
script_dir="$(cd "$(dirname "$0")" && pwd)"
src="$script_dir/../workflows/claude-pr-review.yml"
[ -f "$src" ] || { echo "canonical workflow not found: $src" >&2; exit 2; }
dest_dir="$repo/.github/workflows"
mkdir -p "$dest_dir"
cp "$src" "$dest_dir/claude-review.yml"
echo "Installed $dest_dir/claude-review.yml"
echo "The workflow is off (and free) until the repo opts in. To enable it:"
echo "  gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo <owner>/<repo>   # token from: claude setup-token"
echo "  gh variable set CLAUDE_REVIEW_ENABLED --body true --repo <owner>/<repo>"
echo "  gh label create claude-review --color 5319e7 --repo <owner>/<repo>   # add it to an old PR to review it on demand"
