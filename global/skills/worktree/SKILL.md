---
name: worktree
description: Create or clean up a git worktree for feature work in any repo. Use when starting a new branch, cleaning up after a merged PR, or when the user asks "create a worktree" / "remove worktree" / "clean up worktrees". When multiple agents share a repo, all feature work must happen in worktrees. Per-project branch and path conventions live in the repo's CLAUDE.md.
---

# Git Worktree Management

Multiple Claude Code agents may work on a repo concurrently. A worktree gives each agent an isolated working directory on a shared clone, preventing filesystem conflicts. **Never develop in the main working directory** — if you find yourself editing files in the root clone, stop and create a worktree first.

This is the shared, project-agnostic procedure. The **branch name, worktree path prefix, and first-build setup are defined in the current repo's `CLAUDE.md`** (Git Workflow / Agent Workflow section) — read those before creating one. Conventions currently in use:

| Repo            | Branch                    | Worktree path          |
| --------------- | ------------------------- | ---------------------- |
| WordPower-app   | `feature/wp-<N>-<slug>`   | `../wp-<N>-<slug>`     |
| SliceFocus (BE) | `feature/mer-<N>-<slug>`  | `../sf-be-<N>-<slug>`  |
| SliceFocusFE    | `feature/mer-<N>-<slug>`  | `../sf-fe-<N>-<slug>`  |

If a repo's CLAUDE.md doesn't specify, default to branch `feature/<N>-<slug>` and path `../<repo-shortname>-<N>-<slug>`.

## Create

```bash
git fetch origin
git worktree add "../<PATH>" -b <BRANCH> origin/main
cd "../<PATH>"
# First-build setup for a fresh worktree — run what this repo's CLAUDE.md documents, e.g.:
#   flutter pub get                 # Flutter repos
#   ./mvnw clean generate-sources   # Spring Boot + OpenAPI repos
[ -x ./tool/install-hooks.sh ] && ./tool/install-hooks.sh   # wires per-worktree git hooks if the repo has them
```

Rules:

- **Sibling path only** (`../<prefix>-<N>-<slug>`). Never `.claude/worktrees/` or `.worktrees/` — auto-prune can't reach those. (`claude/*` agent-harness worktrees are the harness's own and are exempt.)
- The path prefix disambiguates repos that share the `~/Projects/` parent (e.g. `sf-be-` / `sf-fe-` / `wp-`), since issue numbers collide across separate repos.
- One worktree per feature branch; one feature branch per issue.

## Clean up (after PR merges)

Run cleanup from the main clone or any directory **outside** the worktree being removed — `git worktree remove` fails if your shell is inside the target worktree.

```bash
cd <main-clone>            # any directory outside the worktree
git worktree remove "../<PATH>"
git worktree prune
git branch -D <BRANCH>      # -D (not -d): squash-merge leaves the branch locally unmerged
```

## Auto-prune (automatic, every repo)

`~/.claude/scripts/prune-worktrees.sh` runs on `SessionStart` for whatever repo you open — wired globally in `~/.claude/settings.json` via `prune-current-worktrees.sh`, which reads the session's `cwd` from the hook payload. It removes worktrees whose branch is gone from `origin` AND whose tree is clean. **Dirty trees and `claude/*` agent-harness branches are left alone.** Because `main` auto-deletes head branches on merge, a merged feature's worktree is swept automatically next session — manual cleanup is rarely needed.

Prune on demand (dry-run first to preview):

```bash
~/.claude/scripts/prune-worktrees.sh <repo-path> --dry-run
~/.claude/scripts/prune-worktrees.sh <repo-path>
```

## Listing

```bash
git worktree list
```
