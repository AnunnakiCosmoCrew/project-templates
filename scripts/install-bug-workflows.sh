#!/usr/bin/env bash
# Install the "bug-close-audit" and "bug-needs-test" workflows into a repo.
# Idempotent: copies both canonical files from workflows/ into
# <repo-dir>/.github/workflows/, substituting the issue-key prefix and bug
# label. Re-run to roll template updates forward.
#
# Usage: install-bug-workflows.sh <repo-dir> <issue-key-prefix> <bug-label>
#   <issue-key-prefix>  this repo's commit-prefix convention, e.g. PEL, HB,
#                       MER, LUV, DVN (emirers/registry.yaml `key` for that
#                       repo). A commit is credited to an issue when its
#                       message contains `#<N>` or `<PREFIX>-<N>`.
#   <bug-label>         the label this repo uses for bug issues/PRs, e.g.
#                       bug. Check with `gh label list --repo <owner>/<repo>`.
#
# Both workflows are EVENT-TRIGGERED (issues: closed / pull_request), not
# cron — they cost nothing until the matching event fires (README
# minute-counting rule).
#
# bug-close-audit.yml needs no further setup: it reopens a bug issue closed
# without a qualifying commit on main in the last 7 days.
#
# bug-needs-test.yml adds a job named "Bug PRs must add test lines", meant
# to be a required status check — add it to the repo's branch-protection
# ruleset once installed. A PR can skip it with the `no-test-required` label
# (explain why in a comment).
set -euo pipefail
usage='usage: install-bug-workflows.sh <repo-dir> <issue-key-prefix> <bug-label>'

repo="${1:?$usage}"
prefix="${2:?$usage}"
label="${3:?$usage}"
[ -d "$repo" ] || { echo "no such repo dir: $repo" >&2; exit 2; }

case "$prefix" in
  [A-Za-z][A-Za-z0-9]*) ;;
  *) echo "issue-key-prefix must start with a letter and contain only letters/digits: $prefix" >&2; exit 2;;
esac
case "$label" in
  ''|*[\"\\/\&\$\'\`]*)
    echo "bug-label must not be empty or contain \", \\, /, &, \$, ' or \`: $label" >&2; exit 2;;
esac

script_dir="$(cd "$(dirname "$0")" && pwd)"
dest_dir="$repo/.github/workflows"
mkdir -p "$dest_dir"

for name in bug-close-audit bug-needs-test; do
  src="$script_dir/../workflows/$name.yml"
  [ -f "$src" ] || { echo "canonical workflow not found: $src" >&2; exit 2; }
  dest="$dest_dir/$name.yml"
  sed -e "s/{{ISSUE_KEY_PREFIX}}/$prefix/g" -e "s/{{BUG_LABEL}}/$label/g" "$src" > "$dest"
  echo "Installed $dest"
done

echo
echo "Labels to create if missing:"
echo "  gh label list --repo <owner>/<repo>"
echo "  gh label create $label --repo <owner>/<repo>   # if this repo has no '$label' label"
echo "  gh label create no-test-required --repo <owner>/<repo>"
echo
echo "bug-needs-test's \"Bug PRs must add test lines\" job is meant to be a"
echo "required status check — add it to the repo's branch-protection ruleset."
