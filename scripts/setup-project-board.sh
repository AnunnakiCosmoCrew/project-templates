#!/usr/bin/env bash
#
# setup-project-board.sh — ensure a GitHub Project (v2) has the AnunnakiCosmoCrew
# standard fields. Idempotent: re-running is safe.
#
# Standard fields ensured:
#   - Status      (single-select: Backlog, Todo, In Progress, In Review, Done, Blocked)
#   - Priority    (single-select: Urgent, High, Medium, Low)
#   - Estimate    (number — Fibonacci 0, 1, 2, 3, 5, 8, 13)
#   - Model & Effort (text — recommended Claude model + effort, e.g., "Sonnet 4.6, medium")
#   - Dependent   (text — comma-separated issue numbers this is blocked by)
#
# Fields that already exist are left untouched. This is so projects that prefer
# P0/P1/P2 over Urgent/High/Medium/Low (etc.) keep their own option scheme — the
# contract is that the *field* exists, not that its options match.
#
# Usage:
#   setup-project-board.sh <owner> <project-number>
#
# Example:
#   setup-project-board.sh AnunnakiCosmoCrew 12
#
# Requires: gh CLI authenticated with `project` and `read:org` scopes.

set -euo pipefail

OWNER="${1:?usage: setup-project-board.sh <owner> <project-number>}"
NUMBER="${2:?usage: setup-project-board.sh <owner> <project-number>}"

echo "→ inspecting project $OWNER/projects/$NUMBER"

PROJECT_JSON=$(gh api graphql -f query="
query {
  organization(login: \"$OWNER\") {
    projectV2(number: $NUMBER) {
      id
      title
      fields(first: 50) {
        nodes {
          ... on ProjectV2FieldCommon { name }
        }
      }
    }
  }
}")

PROJECT_ID=$(echo "$PROJECT_JSON" | jq -r '.data.organization.projectV2.id')
PROJECT_TITLE=$(echo "$PROJECT_JSON" | jq -r '.data.organization.projectV2.title')
EXISTING=$(echo "$PROJECT_JSON" | jq -r '.data.organization.projectV2.fields.nodes[].name')

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "null" ]; then
  echo "✗ project not found or no access" >&2
  exit 1
fi

echo "  project: \"$PROJECT_TITLE\" ($PROJECT_ID)"
echo "  existing fields:"
echo "$EXISTING" | sed 's/^/    - /'
echo

has_field() {
  echo "$EXISTING" | grep -Fxq "$1"
}

create_simple_field() {
  local name="$1"
  local data_type="$2"

  if has_field "$name"; then
    echo "✓ '$name' already exists, skipping"
    return
  fi

  echo "→ creating '$name' ($data_type)"
  gh api graphql -f query="
    mutation {
      createProjectV2Field(input: {
        projectId: \"$PROJECT_ID\",
        dataType: $data_type,
        name: \"$name\"
      }) {
        projectV2Field { ... on ProjectV2FieldCommon { id name } }
      }
    }" > /dev/null
  echo "  ✓ created"
}

create_single_select_field() {
  local name="$1"
  local options_json="$2"  # JSON array of {name, color, description}

  if has_field "$name"; then
    echo "✓ '$name' already exists, skipping (options left as-is)"
    return
  fi

  echo "→ creating '$name' (SINGLE_SELECT)"

  # Build the options literal for GraphQL. createProjectV2Field takes an
  # input list of {name, color, description}.
  local opts
  opts=$(echo "$options_json" | jq -c '
    map("{name: \"" + .name + "\", color: " + .color + ", description: \"" + .description + "\"}")
    | join(", ")
  ' | sed 's/^"//; s/"$//')

  gh api graphql -f query="
    mutation {
      createProjectV2Field(input: {
        projectId: \"$PROJECT_ID\",
        dataType: SINGLE_SELECT,
        name: \"$name\",
        singleSelectOptions: [$opts]
      }) {
        projectV2Field { ... on ProjectV2FieldCommon { id name } }
      }
    }" > /dev/null
  echo "  ✓ created"
}

# --- Standard fields --------------------------------------------------------

create_single_select_field "Status" '[
  {"name": "Backlog",     "color": "GRAY",   "description": "Filed, not yet scheduled"},
  {"name": "Todo",        "color": "PURPLE", "description": "Refined and ready to pick up"},
  {"name": "In Progress", "color": "YELLOW", "description": "Actively being worked"},
  {"name": "In Review",   "color": "BLUE",   "description": "PR open, awaiting merge"},
  {"name": "Done",        "color": "GREEN",  "description": "Merged or closed"},
  {"name": "Blocked",     "color": "RED",    "description": "Waiting on a dependency"}
]'

create_single_select_field "Priority" '[
  {"name": "Urgent", "color": "RED",    "description": "P0 — drop other work"},
  {"name": "High",   "color": "ORANGE", "description": "P1 — schedule this sprint"},
  {"name": "Medium", "color": "YELLOW", "description": "P2 — schedule when capacity allows"},
  {"name": "Low",    "color": "GRAY",   "description": "P3 — nice to have"}
]'

create_simple_field "Estimate" "NUMBER"
create_simple_field "Model & Effort" "TEXT"
create_simple_field "Dependent" "TEXT"

echo
echo "✓ done. Project $OWNER/projects/$NUMBER now satisfies the standard field contract."
