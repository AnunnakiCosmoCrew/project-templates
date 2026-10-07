---
name: issue-start
description: Begin work on a {{PROJECT_NAME}} GitHub issue — set board fields, create the feature branch + worktree, and move the ticket to In Progress. Use when the user says "start issue #N", "pick up {{ISSUE_PREFIX}}-N", "let's work on #N", or otherwise initiates work on a tracked issue. Do NOT use for ad-hoc work without an issue.
---

<!-- TEMPLATE NOTE (stripped by install-workflow.sh):
  Scaffolded into a repo by project-templates/scripts/install-workflow.sh, which fills
  the placeholder values. The worktree recipe is the GLOBAL `worktree` skill
  (~/.claude/skills/worktree) — not duplicated here.
-->

# Starting a {{PROJECT_NAME}} Issue

Project board #{{PROJECT_BOARD_NUMBER}} (`{{REPO_OWNER}}` org) must reflect current state at all times. These steps run **before any code**.

## 1. Read the issue

```bash
gh issue view <N> --repo {{REPO_OWNER}}/{{APP_REPO}} --json title,body,labels,projectItems
```

Confirm with the user if scope is ambiguous. Note the labels — `bug` triggers Test-Driven Bug Fixing (a failing reproducer test commit **before** the fix; see CLAUDE.md).

## 2. Ensure issue is on the project board

```bash
gh project item-add {{PROJECT_BOARD_NUMBER}} --owner {{REPO_OWNER}} --url <issue-url>
```

Idempotent — safe to re-run. Issues created via `gh issue create` are NOT auto-added.

## 3. Set board fields

All required before code:

- **Status** → `In Progress`
- **Priority** → ask the user if not obvious from the issue body.
- **Estimate** → Fibonacci `0, 1, 2, 3, 5, 8, 13`. Bugs are always `0`. The `gh` CLI refuses `--number 0` — use the raw `updateProjectV2ItemFieldValue` GraphQL mutation for bug estimates.
- **Model & Effort** → `Model · tier (reason)` per the global CLAUDE.md, e.g. `Sonnet 5.5 · medium (routine endpoint)`.
- **Dependencies** → an issue with an open native "Blocked by" link is `Blocked`; do not start it. `Dependent` on the board is only a readable mirror of those links.

Use `gh project item-edit` with the field IDs. If you don't have them cached, run `gh project field-list {{PROJECT_BOARD_NUMBER}} --owner {{REPO_OWNER}} --format json` once and reuse.

## 4. Create the worktree + branch

Branch `{{BRANCH_PREFIX}}-<N>-<slug>` (lowercase kebab), worktree at `../{{WORKTREE_PREFIX}}-<N>-<slug>`. See the global `worktree` skill for the recipe.

## 5. Implement and verify

Run the project's local checks before commit (see "Build / Test / Lint Commands" in CLAUDE.md). For `bug` labels, write the failing reproducer test and commit it **first** (`{{ISSUE_PREFIX}}-<N> test: reproduce <bug>`), then the fix (`{{ISSUE_PREFIX}}-<N> fix(<scope>): <what>`).

## 6. Closing the loop — open the PR

Once implementation is finished and local checks pass:

1. Commit using `{{ISSUE_PREFIX}}-<N> <type>[(<scope>)]: description`.
2. Push with `-u` to `origin`.
3. Transition into the `pr-open` skill — it handles the PR body (`Closes #<N>`), required checks, Copilot review watching, and thread resolution.
4. Notify the user when the PR is green and Copilot threads are resolved.

Do not stop after pushing — the agent owns the PR + Copilot loop unless the user says otherwise.

## Do NOT skip

Steps 2–3 are mandatory. The board is the source of truth — silently working without updating it is the failure mode this skill exists to prevent.
