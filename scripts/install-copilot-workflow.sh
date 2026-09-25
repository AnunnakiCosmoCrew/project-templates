#!/usr/bin/env bash
# Install the standard "Resolve Copilot review comments" GitHub Actions workflow
# into a repo. Idempotent: copies the canonical workflow from this templates repo
# to <repo>/.github/workflows/resolve-copilot-comments.yml (overwriting an older
# copy so template updates roll forward).
#
# Usage:
#   install-copilot-workflow.sh <repo-dir> ["<PR check workflow name>"]
#
# The workflow runs after the repo's own PR check workflow finishes
# (`workflow_run`), so it needs that workflow's `name:`, which differs per repo
# ("PR Quality & Security Checks" in Pelerin, "Build" in Pelerin-web). Pass it
# as the second argument, or leave it out and the script uses, in order:
#   1. the name already in an installed copy (re-runs keep what was chosen);
#   2. the one workflow in <repo>/.github/workflows that runs on `pull_request`.
# If neither settles it, the script lists the candidates and stops.
#
# Secret: the Claude step needs ANTHROPIC_API_KEY as a REPOSITORY secret:
#   gh secret set ANTHROPIC_API_KEY --repo <owner>/<repo>
# On the org's GitHub Free plan an organization secret does not reach a private
# repo. The key is optional: without it the workflow warns and skips the Claude
# job instead of failing. A PUBLIC repo does see an org secret whose visibility
# is `all`, so there the workflow is live as soon as it's installed. Either way
# the key bills the Anthropic API account.
set -euo pipefail

placeholder='{{PR_CHECK_WORKFLOW}}'
usage='usage: install-copilot-workflow.sh <repo-dir> ["<PR check workflow name>"]'

repo="${1:?$usage}"
name="${2:-}"
[ -d "$repo" ] || { echo "no such repo dir: $repo" >&2; exit 2; }

script_dir="$(cd "$(dirname "$0")" && pwd)"
src="$script_dir/../workflows/resolve-copilot-comments.yml"
[ -f "$src" ] || { echo "canonical workflow not found: $src" >&2; exit 2; }
[ "$(grep -cF "$placeholder" "$src")" = 1 ] || {
  echo "canonical workflow must contain $placeholder exactly once: $src" >&2; exit 2; }

dest_dir="$repo/.github/workflows"
dest="$dest_dir/resolve-copilot-comments.yml"

# The name GitHub matches `workflow_run.workflows` against: the top-level
# `name:`, or the file's path when there isn't one.
workflow_name() {
  local file="$1" n
  n=$(sed -n -E 's/^name:[[:space:]]*//p' "$file" | head -n 1)
  n=$(printf '%s' "$n" | sed -E -e 's/[[:space:]]+#.*$//' -e 's/[[:space:]]+$//' \
    -e 's/^"(.*)"$/\1/' -e "s/^'(.*)'$/\\1/")
  if [ -n "$n" ]; then
    printf '%s\n' "$n"
  else
    printf '.github/workflows/%s\n' "$(basename "$file")"
  fi
}

# Every other workflow in the repo that runs on `pull_request` (not
# `pull_request_target` or `pull_request_review`), one name per line.
pr_workflows() {
  local f
  [ -d "$dest_dir" ] || return 0
  for f in "$dest_dir"/*.yml "$dest_dir"/*.yaml; do
    [ -f "$f" ] || continue
    [ "$(basename "$f")" = "resolve-copilot-comments.yml" ] && continue
    if grep -v -E '^[[:space:]]*#' "$f" | grep -q -E '(^|[^_[:alnum:]])pull_request([^_[:alnum:]]|$)'; then
      workflow_name "$f"
    fi
  done
}

candidates=$(pr_workflows)

if [ -z "$name" ] && [ -f "$dest" ]; then
  name=$(sed -n -E 's/^[[:space:]]*workflows:[[:space:]]*\["(.*)"\][[:space:]]*$/\1/p' "$dest" | head -n 1)
  [ "$name" = "$placeholder" ] && name=""
  if [ -n "$name" ]; then
    echo "Keeping the PR check workflow from the installed copy: \"$name\""
  fi
fi

if [ -z "$name" ]; then
  count=$(printf '%s' "$candidates" | grep -c . || true)
  if [ "$count" = 1 ]; then
    name="$candidates"
    echo "Using the repo's only pull_request workflow: \"$name\""
  else
    {
      echo "Can't tell which workflow is the PR check in $repo. Pass its name:"
      echo "  $usage"
      if [ "$count" = 0 ]; then
        echo "No workflow in $dest_dir runs on pull_request."
      else
        echo "Workflows that run on pull_request:"
        printf '%s\n' "$candidates" | sed 's/^/  - /'
      fi
    } >&2
    exit 1
  fi
fi

# The name lands inside a double-quoted YAML string.
case "$name" in
  *'"'* | *\\* | *'{{'* | *'}}'* | *$'\n'*)
    echo "workflow name must not contain \", \\, {{, }} or a newline: $name" >&2
    exit 1
    ;;
esac

if ! printf '%s\n' "$candidates" | grep -qxF -- "$name"; then
  echo "warning: no workflow in $dest_dir that runs on pull_request is named \"$name\"." >&2
  echo "         workflow_run will never fire; only the 3-hourly cron and manual runs will." >&2
fi

mkdir -p "$dest_dir"
tmp=$(mktemp "$dest_dir/.resolve-copilot-comments.XXXXXX")
trap 'rm -f "$tmp"' EXIT
PR_CHECK_WORKFLOW="$name" awk -v p="$placeholder" '
  { i = index($0, p)
    if (i > 0) $0 = substr($0, 1, i - 1) ENVIRON["PR_CHECK_WORKFLOW"] substr($0, i + length(p))
    print }' "$src" > "$tmp"
mv "$tmp" "$dest"
echo "Installed $dest (runs after \"$name\")"
echo "Optional: enable the Claude step with a repository secret:"
echo "  gh secret set ANTHROPIC_API_KEY --repo <owner>/<repo>"
