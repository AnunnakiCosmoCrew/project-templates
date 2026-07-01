#!/usr/bin/env bash
# Install the standard "Resolve Copilot review comments" GitHub Actions workflow
# into a repo. Idempotent: copies the canonical workflow from this templates repo
# to <repo>/.github/workflows/resolve-copilot-comments.yml (overwriting an older
# copy so template updates roll forward).
#
# Usage:
#   install-copilot-workflow.sh <repo-dir>
#
# The workflow needs an ANTHROPIC_API_KEY secret. Set it ONCE org-wide so every
# repo inherits it (private repos included):
#   gh secret set ANTHROPIC_API_KEY --org AnunnakiCosmoCrew --visibility all
set -euo pipefail

repo="${1:?usage: install-copilot-workflow.sh <repo-dir>}"
[ -d "$repo" ] || { echo "no such repo dir: $repo" >&2; exit 2; }

script_dir="$(cd "$(dirname "$0")" && pwd)"
src="$script_dir/../workflows/resolve-copilot-comments.yml"
[ -f "$src" ] || { echo "canonical workflow not found: $src" >&2; exit 2; }

dest_dir="$repo/.github/workflows"
mkdir -p "$dest_dir"
cp "$src" "$dest_dir/resolve-copilot-comments.yml"
echo "Installed $dest_dir/resolve-copilot-comments.yml"
