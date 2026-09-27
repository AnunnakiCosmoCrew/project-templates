#!/usr/bin/env bash
# Install the standard "Resolve Copilot review comments" GitHub Actions workflow
# into a repo. Idempotent: copies the canonical workflow from this templates repo
# to <repo>/.github/workflows/resolve-copilot-comments.yml (overwriting an older
# copy so template updates roll forward).
#
# Usage:
#   install-copilot-workflow.sh <repo-dir> ["<PR check workflow name>"]
#   install-copilot-workflow.sh <repo-dir> --no-ci
#
# The workflow runs after the repo's own PR check workflow finishes
# (`workflow_run`), so it needs that workflow's `name:`, which differs per repo
# ("PR Quality & Security Checks" in Pelerin, "Build" in Pelerin-web). Pass it
# as the second argument, or leave it out and the script uses, in order:
#   1. the name already in an installed copy (re-runs keep what was chosen);
#   2. the one workflow in <repo>/.github/workflows that runs on `pull_request`.
# If neither settles it, the script lists the candidates and stops.
#
# For a repo with NO pull_request-triggered CI at all (so there is no name to
# give `workflow_run` — it would just be permanently inert), pass `--no-ci`
# instead of a name. This installs a direct `pull_request: types: [opened,
# synchronize]` trigger alongside the (inert) workflow_run and the cron
# fallback, so the scan still runs promptly rather than only every 3 hours.
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
extra_placeholder='{{EXTRA_TRIGGER}}'
no_ci_name='(no PR-triggered CI in this repo)'
usage='usage: install-copilot-workflow.sh <repo-dir> ["<PR check workflow name>"|--no-ci]'

repo="${1:?$usage}"
arg2="${2:-}"
no_ci=false
name=""
if [ "$arg2" = "--no-ci" ]; then
  no_ci=true
  name="$no_ci_name"
elif [ -n "$arg2" ]; then
  name="$arg2"
fi
[ -d "$repo" ] || { echo "no such repo dir: $repo" >&2; exit 2; }

script_dir="$(cd "$(dirname "$0")" && pwd)"
src="$script_dir/../workflows/resolve-copilot-comments.yml"
[ -f "$src" ] || { echo "canonical workflow not found: $src" >&2; exit 2; }
[ "$(grep -cF "$placeholder" "$src")" = 1 ] || {
  echo "canonical workflow must contain $placeholder exactly once: $src" >&2; exit 2; }
[ "$(grep -cF "$extra_placeholder" "$src")" = 1 ] || {
  echo "canonical workflow must contain $extra_placeholder exactly once: $src" >&2; exit 2; }

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
    if awk '!/^[[:space:]]*#/ && /(^|[^_[:alnum:]])pull_request([^_[:alnum:]]|$)/ { found=1 } END { exit !found }' "$f"; then
      workflow_name "$f"
    fi
  done
}

candidates=$(pr_workflows)

# When no explicit choice was passed, recover the previous choice (including
# no-ci mode) from an already-installed copy, so a bare re-run can't silently
# regress a no-ci repo back to cron-only by losing the pull_request trigger.
if [ -z "$arg2" ] && [ -f "$dest" ]; then
  recovered=$(sed -n -E 's/^[[:space:]]*workflows:[[:space:]]*\["(.*)"\][[:space:]]*$/\1/p' "$dest" | head -n 1)
  if [ "$recovered" = "$no_ci_name" ]; then
    no_ci=true
    name="$no_ci_name"
    echo "Keeping no-ci mode from the installed copy."
  elif [ -n "$recovered" ] && [ "$recovered" != "$placeholder" ]; then
    name="$recovered"
    echo "Keeping the PR check workflow from the installed copy: \"$name\""
  fi
fi

if [ "$no_ci" = true ]; then
  echo "No-CI mode: workflow_run stays inert (sentinel name); adding a direct pull_request trigger instead."
else
  if [ -z "$name" ]; then
    count=$(printf '%s' "$candidates" | grep -c . || true)
    if [ "$count" = 1 ]; then
      name="$candidates"
      echo "Using the repo's only pull_request workflow: \"$name\""
    else
      {
        echo "Can't tell which workflow is the PR check in $repo. Pass its name, or pass --no-ci if this repo has no pull_request-triggered CI:"
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
    echo "         (if that's expected, re-run with --no-ci instead to add a pull_request trigger)" >&2
  fi
fi

if [ "$no_ci" = true ]; then
  extra_trigger='  pull_request_target:
    types: [opened, synchronize]'
else
  extra_trigger=''
fi

mkdir -p "$dest_dir"
tmp=$(mktemp "$dest_dir/.resolve-copilot-comments.XXXXXX")
trap 'rm -f "$tmp"' EXIT
# Literal-line match: the marker occupies its own indented line in the
# canonical file. Empty extra_trigger drops the line; otherwise the line is
# replaced with the (already fully-indented) trigger block. A plain shell loop
# is used instead of awk -v because macOS awk chokes on a -v value containing
# a literal newline.
marker="  $extra_placeholder"
while IFS= read -r line || [ -n "$line" ]; do
  if [ "$line" = "$marker" ]; then
    [ -n "$extra_trigger" ] && printf '%s\n' "$extra_trigger"
  else
    printf '%s\n' "$line"
  fi
done < "$src" > "$tmp"
PR_CHECK_WORKFLOW="$name" awk -v p="$placeholder" '
  { i = index($0, p)
    if (i > 0) $0 = substr($0, 1, i - 1) ENVIRON["PR_CHECK_WORKFLOW"] substr($0, i + length(p))
    print }' "$tmp" > "$tmp.2"
mv "$tmp.2" "$tmp"
mv "$tmp" "$dest"
if [ "$no_ci" = true ]; then
  echo "Installed $dest (no-ci mode: pull_request trigger + 3-hourly cron fallback)"
else
  echo "Installed $dest (runs after \"$name\")"
fi
echo "Optional: enable the Claude step with a repository secret:"
echo "  gh secret set ANTHROPIC_API_KEY --repo <owner>/<repo>"
