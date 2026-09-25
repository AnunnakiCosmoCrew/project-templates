# project-templates

Templates and bootstrap tooling for new AnunnakiCosmoCrew projects. Apply these to a fresh repo + project board to get a working CLAUDE.md and a project board with the standard fields in under a minute.

## What's here

| File | What it does |
| --- | --- |
| [`CLAUDE.template.md`](CLAUDE.template.md) | Parameterized CLAUDE.md skeleton. Copy → fill placeholders → drop into the new repo as `CLAUDE.md`. |
| [`scripts/setup-project-board.sh`](scripts/setup-project-board.sh) | Idempotent script that ensures a GitHub Project (v2) board has the standard fields. |
| [`workflows/resolve-copilot-comments.yml`](workflows/resolve-copilot-comments.yml) | Canonical "Resolve Copilot review comments" GitHub Actions workflow. When Copilot reviews a PR, Claude applies the valid fixes, pushes them, and resolves the threads. |
| [`scripts/install-copilot-workflow.sh`](scripts/install-copilot-workflow.sh) | Copies the Copilot-resolve workflow into a repo's `.github/workflows/`, filling in the name of that repo's PR check workflow. Idempotent. |

## The contract

Any project that adopts these templates commits to a board with at least these fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `Status` | single-select | Backlog → Todo → In Progress → In Review → Done (+ Blocked) |
| `Priority` | single-select | Urgent / High / Medium / Low |
| `Estimate` | number | Fibonacci story points (0, 1, 2, 3, 5, 8, 13) |
| `Model & Effort` | text | Recommended Claude model + effort, e.g., `Sonnet 4.6, medium` |
| `Dependent` | text | Comma-separated issue numbers this is blocked by, e.g., `#412, #420` |

GitHub's native `Parent issue` and `Sub-issues progress` fields are also part of the workflow but exist on every project board by default — no setup needed.

The script is **idempotent and non-destructive**. If a field already exists, it's left alone — including its options. Projects that prefer `P0/P1/P2` over `Urgent/High/Medium/Low` (etc.) keep their local taste; the contract is just that the field exists.

## Copilot review auto-resolve (all repos)

Every repo gets the **"Resolve Copilot review comments"** workflow
([`workflows/resolve-copilot-comments.yml`](workflows/resolve-copilot-comments.yml)).
When GitHub Copilot (`copilot-pull-request-reviewer[bot]`) reviews a PR, Claude runs
in CI, applies the valid suggestions, pushes the fixes to the PR branch, and resolves
the threads it addressed — so nobody has to hand-resolve Copilot's comments each session.

- **Code repos:** required — the workflow belongs on every code repo.
- **Docs repos:** recommended but optional. PRs there are optional (docs often land
  straight on `main`), so a Copilot review isn't guaranteed — the workflow just stays
  dormant until a PR actually gets one.

**When it runs.** It does *not* trigger on `pull_request_review`: GitHub gates runs
started by Copilot's review bot as `action_required` with zero jobs, even on same-repo
private PRs, so the job never ran. It runs on:

- `workflow_run` of the repo's own **PR check workflow** (`types: [completed]`), skipped
  when that run wasn't for a pull request;
- a sparse `0 */3 * * *` cron as a fallback for a review that lands late;
- `workflow_dispatch`, optionally forced to one PR number.

A cheap `find-prs` job scans open PRs for an unresolved, unreplied Copilot thread and
only then starts the Claude job. **Don't reintroduce a 15-minute cron**: each poll
bills a full minute, about 2,900 minutes a month per repo, more than the org's whole
GitHub Free allowance.

**The API key is a repository secret, and optional.** On the org's GitHub Free plan an
*organization* secret does not reach a *private* repo, so the key has to be set per repo:

```bash
gh secret set ANTHROPIC_API_KEY --repo AnunnakiCosmoCrew/<repo>
```

Without it, `find-prs` logs a warning and outputs no PRs, so the Claude job is skipped
instead of failing. The key bills the Anthropic **API** account, not the Claude
subscription. Decision 2026-09-25: leave it unset and the workflow dormant.

> **Don't set it at the org level.** An org secret with visibility `all` *does* reach a
> public repo, so it would make the workflow live on every public repo that carries it.
> The org had such an `ANTHROPIC_API_KEY` (set 2026-07-01); it was deleted on 2026-09-25,
> and no repo has a repository-level one, so the workflow is dormant org-wide.

**Install it into a repo** (idempotent — re-run to roll template updates forward). The
second argument is the `name:` of that repo's PR check workflow, which differs per repo:

```bash
./scripts/install-copilot-workflow.sh ~/Projects/Pelerin "PR Quality & Security Checks"
./scripts/install-copilot-workflow.sh ~/Projects/Pelerin-web "Build"
```

The canonical file carries a `{{PR_CHECK_WORKFLOW}}` placeholder the script fills in.
Leave the name out and the script reuses the one in an already-installed copy, or picks
the repo's only `pull_request` workflow. If there are several, it lists them and stops.

## Bootstrap a new project

```bash
# 1. Create the repo and project board (manually or via gh repo create + gh project create)
gh repo create AnunnakiCosmoCrew/new-thing --public
gh project create --owner AnunnakiCosmoCrew --title "New Thing"   # note the project number

# 2. Ensure standard board fields exist
./scripts/setup-project-board.sh AnunnakiCosmoCrew <project-number>

# 3. Drop the CLAUDE.md template into the new repo
curl -sL https://raw.githubusercontent.com/AnunnakiCosmoCrew/project-templates/main/CLAUDE.template.md \
  -o CLAUDE.md

# 4. Open CLAUDE.md, replace every {{PLACEHOLDER}}, delete the <!-- OPTIONAL --> blocks
#    you don't need, and fill in the <!-- FILL --> sections with your stack's
#    actual commands.

# 5. Add the Copilot review auto-resolve workflow (from this repo's checkout), naming
#    the new repo's PR check workflow. It stays dormant until a repository
#    ANTHROPIC_API_KEY is set (see above; public repos differ).
./scripts/install-copilot-workflow.sh /path/to/new-thing "<PR check workflow name>"

# 6. Commit and push.
git add CLAUDE.md .github/workflows/resolve-copilot-comments.yml
git commit -m "chore: add CLAUDE.md + Copilot-resolve workflow (from project-templates)"
git push
```

## Maintaining the templates

When the conventions evolve (new field, new workflow step, etc.):

1. Update the relevant source here: `CLAUDE.template.md`, `workflows/resolve-copilot-comments.yml`, or `scripts/`.
2. Note the change in this README under "Version history" below.
3. Open a PR in each adopting project to roll the change forward — nothing here is auto-applied to existing projects. For the Copilot workflow specifically, that means re-running `./scripts/install-copilot-workflow.sh <repo-dir>` against each adopting repo (pass the PR check workflow name the first time) and opening a PR with the result.

## Adopting projects

| Project | CLAUDE.md | Board | Adopted |
| --- | --- | --- | --- |
| WordPower | [`WordPower-app/CLAUDE.md`](https://github.com/AnunnakiCosmoCrew/WordPower-app/blob/main/CLAUDE.md) | [#11](https://github.com/orgs/AnunnakiCosmoCrew/projects/11) | reference implementation |
| Magpie | [`magpie-app-private/CLAUDE.md`](https://github.com/AnunnakiCosmoCrew/magpie-app-private/blob/main/CLAUDE.md) | [#12](https://github.com/orgs/AnunnakiCosmoCrew/projects/12) | 2026-05-12 |

## Version history

- **2026-09-25** — Ported Pelerin's fix for the Copilot-resolve trigger ([AnunnakiCosmoCrew/Pelerin#129](https://github.com/AnunnakiCosmoCrew/Pelerin/pull/129), then [#148](https://github.com/AnunnakiCosmoCrew/Pelerin/pull/148)): `pull_request_review` never ran (GitHub gates the Copilot bot's runs as `action_required`), so the workflow now runs on `workflow_run` of the repo's PR check workflow, with a sparse `0 */3 * * *` cron fallback and `workflow_dispatch`. A `find-prs` job picks the PRs to process, and skips with a warning when `ANTHROPIC_API_KEY` isn't visible. The PR check workflow's name is a `{{PR_CHECK_WORKFLOW}}` placeholder that `install-copilot-workflow.sh` fills in per repo. The trust boundary from the previous entry is kept; Pelerin's copy doesn't have it. Corrected the docs: the key is an optional **repository** secret, because an org secret doesn't reach private repos on GitHub Free. It does reach public repos, so the org-level `ANTHROPIC_API_KEY` (visibility `all`) was deleted the same day, and this repo's own dogfooded copy is removed rather than kept in sync.
- **2026-09-22** — Closed the privileged-execution hole the first pass left open: the workflow no longer asks Claude to run the project's build/tests/lint (that was PR-authored code executing in a job that holds a write-capable token and the org `ANTHROPIC_API_KEY`), and `--allowedTools` now grants only `gh` and `git` instead of blanket `Bash`. Verification moves to the repo's own CI, which runs on the pushed commit and gates the merge anyway. Added a TRUST BOUNDARY comment to the workflow recording why the fork-PR check is necessary but not sufficient. Raised by Copilot review on #3.
- **2026-09-22** — Hardened `workflows/resolve-copilot-comments.yml`: SHA-pinned `anthropics/claude-code-action` (was a floating `@v1` tag), added a per-PR `concurrency` guard, restored the fork-PR safety check the header comment already claimed (`head.repo.full_name == github.repository`), bumped `actions/checkout` to v7, and added explicit `persist-credentials`/`GH_TOKEN`. Picked by auditing the 6 variants the file had already drifted into across 38 adopting repos and choosing the most complete, most recently maintained one (Pelerin's). Re-syncing already-adopting repos is a separate follow-up.
- **2026-07-01** — Added the standard **"Resolve Copilot review comments"** GitHub Actions workflow (`workflows/resolve-copilot-comments.yml`) + `install-copilot-workflow.sh`, and rolled it out to all org repos via PRs. Needs a one-time org-level `ANTHROPIC_API_KEY` secret.
- **2026-05-12** — Initial templates. CLAUDE.md skeleton extracted from WordPower-app/CLAUDE.md after WP-565 (added `Dependent` field workflow, closed WP-29 staleness). `setup-project-board.sh` ensures Status, Priority, Estimate, Model & Effort, Dependent fields exist.
