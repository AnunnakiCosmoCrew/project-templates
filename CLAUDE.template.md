<!--
============================================================================
CLAUDE.md template — AnunnakiCosmoCrew

How to use:
  1. Copy this file to the new repo as CLAUDE.md.
  2. Replace every {{PLACEHOLDER}} with the project-specific value.
  3. Delete any <!-- OPTIONAL: ... --> section that doesn't apply.
  4. Fill the <!-- FILL: ... --> sections with your stack's commands.
  5. Run scripts/setup-project-board.sh to ensure the board has the
     fields this CLAUDE.md references.

Placeholders (all required unless noted):
  {{PROJECT_NAME}}            e.g., "Magpie", "WordPower"
  {{PROJECT_TAGLINE}}         one-line description
  {{PROJECT_OVERVIEW}}        2-4 sentence project overview
  {{REPO_OWNER}}              GitHub org, e.g., "AnunnakiCosmoCrew"
  {{APP_REPO}}                code repo name, e.g., "magpie-app-private"
  {{DOCS_REPO}}               docs repo name, e.g., "magpie-docs"
  {{PUBLIC_REPO}}             optional public placeholder, e.g., "magpie"; remove if N/A
  {{PROJECT_BOARD_NUMBER}}    e.g., 11
  {{ISSUE_PREFIX}}            short code in caps, e.g., "WP", "MAG"
  {{BRANCH_PREFIX}}           lowercase prefix, e.g., "feature/wp", "feature/mag"
  {{COMMIT_PREFIX_EXAMPLE}}   e.g., "WP-42", "MAG-7"
  {{TECH_STACK_DESCRIPTION}}  one-paragraph stack summary
============================================================================
-->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

{{PROJECT_TAGLINE}}.

{{PROJECT_OVERVIEW}}

## Repository Map

<!-- FILL: replace the table below with your project's actual repo map. -->

| Repo | Purpose | Push to main? |
| --- | --- | --- |
| `{{REPO_OWNER}}/{{APP_REPO}}` (this repo) | <!-- FILL: what this repo holds --> | No — branch + PR only |
| `{{REPO_OWNER}}/{{DOCS_REPO}}` | Charter, design notes, ADR drafts, launch playbook | Yes — direct push |
<!-- OPTIONAL: PUBLIC_REPO row — delete if the project has no public/private split. -->
| `{{REPO_OWNER}}/{{PUBLIC_REPO}}` | Public-facing repo (name placeholder until first release) | No — populated via curated cutover only |
<!-- /OPTIONAL -->

## Tech Stack

{{TECH_STACK_DESCRIPTION}}

## Build / Test / Lint Commands

<!-- FILL: replace the placeholder blocks below with your real commands.
     Keep the section names ("Build", "Test", "Lint") so commits/PRs can
     reference them consistently across projects. -->

```
# Build:          <FILL>
# Test:           <FILL>
# Lint / format:  <FILL>
# Single test:    <FILL>
```

## Git Workflow (Trunk-Based Development)

`main` is the single integration branch. All code changes land via short-lived feature branches and squash-merge PRs.

**Never push directly to main** — always create a branch and PR, even for one-line changes.

### Branch naming

`{{BRANCH_PREFIX}}-{N}-{slug}` where `{N}` is the GitHub Issue number (lowercase, e.g., `{{BRANCH_PREFIX}}-42-quick-capture-screen`).

### Commit message format

`{{ISSUE_PREFIX}}-{N} <type>[(<scope>)]: description`

Types: `feat`, `fix`, `chore`, `test`, `docs`, `refactor`, `perf`, `ci`

Examples:

- `{{COMMIT_PREFIX_EXAMPLE}} feat(scope): describe the new capability`
- `{{COMMIT_PREFIX_EXAMPLE}} fix(scope): describe the bug being closed`
- `{{COMMIT_PREFIX_EXAMPLE}} test: reproduce the bug from issue body`

### Issue Workflow — Follow for Every GitHub Issue

1. **Add issue to the project board** when creating via `gh issue create` (it does NOT auto-add). Use `gh project item-add {{PROJECT_BOARD_NUMBER}} --owner {{REPO_OWNER}} --url <issue-url>`. Then set board fields: `Status`, `Priority`, `Estimate`, `Model & Effort`, and `Dependent` (if applicable — see "Dependent vs. sub-issues" below).
2. **Set an estimate** (Fibonacci: 0, 1, 2, 3, 5, 8, 13) on the project board. Bugs are `0`.
3. **Set the `Model & Effort`** on the project board; that represents the most optimal Claude.ai model and effort for the task (e.g., `Sonnet 4.6, medium`).
4. **Set `Dependent`** if this issue is blocked by other issues — comma-separated list of issue numbers (e.g., `#412, #420`). Leave blank otherwise.
5. **Move ticket to "In Progress"** on the project board before writing any code.
6. **Create a feature branch** from latest `main`: `{{BRANCH_PREFIX}}-{N}-{slug}`.
7. **Implement and verify**: run the commands from "Build / Test / Lint Commands" above. All must pass before pushing.
8. **Commit** to the feature branch with a descriptive message referencing the issue number.
9. **Push and open a PR** with `Closes #NNN` in the body so the issue auto-closes on merge.

> **Do NOT skip steps 1–5.** The project board must reflect the current state of work at all times.

### Dependent vs. sub-issues

The board exposes two related fields for capturing how issues relate to each other. Choose deliberately:

- **`Dependent`** (text field). Use when this issue is *blocked by* one or more **peer** issues — same scope tier, not nested. Set the value to a comma-separated list of issue numbers, e.g., `#412, #420`. Read as "this is dependent on those". Update or clear it as blockers resolve.
- **`Parent issue` + `Sub-issues progress`** (GitHub-native sub-issues). Use when this issue is one *step inside* a larger one. The parent is the umbrella, the children are the decomposition. Progress on the parent updates automatically as children close.

**Heuristic:** if one issue can't start until another finishes but they aren't parts of the same larger thing, use `Dependent`. If they're slices of the same larger thing, use sub-issues. The two are not mutually exclusive — a child of one parent can also be `Dependent` on an unrelated peer.

### Bug Fixes — Test-Driven Bug Fixing (TDBF)

When fixing a bug, the failing test that reproduces it must be written and committed *before* the fix. Two commits on the same branch:

1. **Red commit** — test that reproduces the bug (test will fail by design; lint/analyze must still pass). Commit: `{{ISSUE_PREFIX}}-{N} test: reproduce <bug description>`.
2. **Green commit** — the fix. All tests pass. Commit: `{{ISSUE_PREFIX}}-{N} fix(<scope>): <what the fix does>`.

### Branch Protection

Currently enforced on `main`:

- Squash merge only (merge commits and rebase disabled)
- Auto-delete head branches after merge
- Force push blocked
- Branch deletion blocked
- Pull request required before merging
- **All review conversations must be resolved** (reply **and** explicitly resolve threads)

<!-- OPTIONAL: required-status-checks. Enable once your CI is stable; until
     then, delete this bullet so you can merge without ghost-blocking checks. -->
- **Required status checks** — a PR will not merge until ALL of:
  - <!-- FILL: e.g., `Build and test` (Backend CI) -->
  - <!-- FILL: e.g., `Analyze, format, test` (Frontend CI) -->
  - <!-- FILL: e.g., `Static analysis` (Semgrep SAST) -->
<!-- /OPTIONAL -->

<!-- OPTIONAL: Copilot review. Delete this whole section if Copilot review
     isn't enabled on this repo yet. -->
### Copilot Code Review

Every PR is auto-reviewed by GitHub Copilot (enabled at the org/repo level). Treat Copilot review like a human review:

- **Any thread Copilot opens must be addressed** — reply explaining the fix (or why no change is needed) **and** explicitly resolve the thread.
- This is enforced by `required_conversation_resolution` on `main` — merges block until every Copilot (and human) thread is resolved.
- Copilot uses `.github/copilot-instructions.md` for project context — keep that file up to date when conventions change.
- **If Copilot doesn't post a review within ~6 minutes** of PR open, consider adding a `copilot-nudge` workflow that removes + re-adds Copilot to the requested reviewers — that's the empirically-reliable way to retrigger the bot when it silently skips a PR.
<!-- /OPTIONAL -->

## Agent Workflow

Multiple Claude Code agents may work on this repo concurrently. To prevent filesystem conflicts, every agent **must** develop inside a dedicated `git worktree` — never directly in the main working directory.

### Creating a worktree

```bash
# From the main working directory
git fetch origin
git worktree add "../{{BRANCH_PREFIX}#feature/}-{N}-{slug}" -b {{BRANCH_PREFIX}}-{N}-{slug} origin/main
```

This creates a sibling directory checked out to the new branch. All build, test, and commit commands run from inside that directory.

### Cleaning up

```bash
# After the PR is merged
git worktree remove "../{{BRANCH_PREFIX}#feature/}-{N}-{slug}"
git worktree prune
git branch -D {{BRANCH_PREFIX}}-{N}-{slug}  # -D because squash-merge leaves the branch locally unmerged
```

### Rules

- **Never develop in the main working directory.** If you find yourself editing files in the root clone, stop and create a worktree first.
- One worktree per feature branch; one feature branch per issue.
- The worktree path should match the branch slug for clarity.

## Project Management

- **Project board**: GitHub Projects board #{{PROJECT_BOARD_NUMBER}} (`{{REPO_OWNER}}` org)
- **Issue tracking**: GitHub Issues on this repo + the project board
- **Board fields**: `Status`, `Priority`, `Estimate` (Fibonacci 0, 1, 2, 3, 5, 8, 13), `Model & Effort`, `Dependent` (blocking peer issues), `Parent issue` (for sub-issue decomposition)
- **Architecture decisions**: Documented in `{{REPO_OWNER}}/{{DOCS_REPO}}` (drafts) and promoted to `docs/decisions/` here when accepted
