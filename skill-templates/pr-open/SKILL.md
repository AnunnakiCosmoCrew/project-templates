---
name: pr-open
description: Open a pull request for a {{PROJECT_NAME}} feature branch, then watch for Copilot review and resolve threads. Use when the user says "open the PR", "ship it", "create a PR", or after pushing a feature branch that's ready for review. Handles the required-checks list and Copilot thread resolution.
---

<!-- TEMPLATE NOTE (stripped by install-workflow.sh):
  Scaffolded into a repo by project-templates/scripts/install-workflow.sh, which fills
  the placeholder values. After install, complete the FILL note in section 3 with this
  repo's actual required-check names.
-->

# Opening a {{PROJECT_NAME}} PR

## 1. Pre-flight

- Branch is pushed to `origin` with `-u`.
- All local checks pass (see "Build / Test / Lint Commands" in CLAUDE.md).
- For `bug` branches: the two-commit red→green pattern is present (reproducer test before the fix).
- You are in a worktree, not the main working directory (see the `worktree` skill).

## 2. Create the PR

```bash
gh pr create --repo {{REPO_OWNER}}/{{APP_REPO}} \
  --title "{{ISSUE_PREFIX}}-<N> <type>: description" \
  --body "..."
```

Required body elements:

- `Closes #<N>` (or `Closes {{REPO_OWNER}}/<repo>#<N>` for cross-repo issues) — so the issue auto-closes on merge.
- Summary: 1–3 bullets on *why*, not *what*.
- Test plan: bulleted checklist.
- For `bug` PRs: proof-of-fix (screenshot / curl / log output).

## 3. Required status checks

A PR will not merge until ALL pass:

<!-- FILL: list this repo's required checks, e.g.
- `Build and test` (Backend CI)
- `Analyze, format, test` (Frontend CI)
- `Static analysis` (Semgrep SAST)
-->

If a required check is missing entirely, GitHub treats "did not run" as a blocker — fix the workflow, don't bypass.

## 4. Copilot review

Every PR is auto-reviewed by GitHub Copilot. Treat it like a human review.

- **Every Copilot thread must be addressed**: reply with the fix (or justification), then explicitly resolve the thread via the GitHub UI or the `resolveReviewThread` GraphQL mutation. The `main-protection` ruleset blocks the merge otherwise, and `git-guard.py` refuses `gh pr merge` while a thread is open — replying alone does not resolve.
- After opening the PR, **watch for the review autonomously**, resolve threads as they appear, and notify the user when everything is resolved and ready for their final merge call.

## 5. Hard rules

- **Never push directly to main** — even for one-line changes. The ruleset refuses it server-side and `git-guard.py` refuses it locally.
- **Never bypass branch protection** (`--admin`, force-push, skip required checks). `git-guard.py` refuses `gh pr merge --admin` and a merge with red, pending or skipped required checks.
- **Squash merge only.** No merge commits, no rebase merges.
- **Auto-delete head branches** is on — the remote branch is removed on merge; the local worktree is swept by auto-prune next session (see the `worktree` skill).
