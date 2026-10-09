---
name: pr-open
description: Open a pull request for a {{PROJECT_NAME}} feature branch, then watch for the Claude review and resolve threads. Use when the user says "open the PR", "ship it", "create a PR", or after pushing a feature branch that's ready for review. Handles the required-checks list and review-thread resolution.
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
- `Founder check:` line (see section 4a): `Founder check: none`, or `Founder check: <tier>: <what the founder should verify>`.

## 3. Required status checks

A PR will not merge until ALL pass:

<!-- FILL: list this repo's required checks, e.g.
- `Build and test` (Backend CI)
- `Analyze, format, test` (Frontend CI)
- `Static analysis` (Semgrep SAST)
-->

If a required check is missing entirely, GitHub treats "did not run" as a blocker — fix the workflow, don't bypass.

## 4. Claude review

Every new non-draft PR is reviewed by the Claude PR review workflow (inline comments plus one summary review). Treat it like a human review.

- **Every review thread must be addressed** (Claude's, a human's, or Copilot's if it runs): reply with the fix (or justification), then explicitly resolve the thread via the GitHub UI or the `resolveReviewThread` GraphQL mutation. The `main-protection` ruleset blocks the merge otherwise, and `git-guard.py` refuses `gh pr merge` while a thread is open — replying alone does not resolve.
- **Draft-first PRs:** a draft is not reviewed automatically. Add the `claude-review` label to review it as a draft (`gh pr edit <N> --add-label claude-review`), resolve the threads, push once, then `gh pr ready`. A labelled PR is not reviewed again when it is marked ready.
- After opening the PR, **watch for the review autonomously**, resolve threads as they appear, and notify the user when everything is resolved and ready for their final merge call.

## 4a. Founder review is risk-tiered

The founder's review is for founder-tier PRs only (luvita-docs ADR 0004). Everything else merges on green required checks, resolved threads and the Claude review.

A PR is founder-tier when it touches:

- **Irreversible ops:** production deploys or release tags, data migrations, deleting infrastructure.
- **Money:** billing, Actions minutes (new or heavier workflows, schedules, macOS runners), cloud resources.
- **Public-facing content:** site copy, brand or product claims, App Store / Play metadata, legally sensitive claims.
- **Security and access:** `.github/workflows/`, secrets, auth, permissions, rulesets, `CODEOWNERS`, Claude Code settings.
- **Product or UX decisions** the issue did not specify and the agent made on its own.

When in doubt, it is founder-tier. Say which tier and what to verify on the `Founder check:` line. Never add the founder as a reviewer by hand. A local session acts as the founder's login, and GitHub refuses a review request to the PR's author. EmirErs requests the review on founder-tier cloud PRs. A local session names a founder-tier PR as such when it hands over.

## 5. Hard rules

- **Never push directly to main** — even for one-line changes. The ruleset refuses it server-side and `git-guard.py` refuses it locally.
- **Never bypass branch protection** (`--admin`, force-push, skip required checks). `git-guard.py` refuses `gh pr merge --admin` and a merge with red, pending or skipped required checks.
- **Squash merge only.** No merge commits, no rebase merges.
- **Auto-delete head branches** is on — the remote branch is removed on merge; the local worktree is swept by auto-prune next session (see the `worktree` skill).
