# project-templates

Templates and bootstrap tooling for new AnunnakiCosmoCrew projects. Apply these to a fresh repo + project board to get a working CLAUDE.md and a project board with the standard fields in under a minute.

## What's here

| File | What it does |
| --- | --- |
| [`CLAUDE.template.md`](CLAUDE.template.md) | Parameterized CLAUDE.md skeleton. Copy → fill placeholders → drop into the new repo as `CLAUDE.md`. |
| [`skill-templates/`](skill-templates) | Parameterized `issue-start` + `pr-open` skills, scaffolded per repo by `install-workflow.sh`. |
| [`global/`](global) | Canonical copy of the one generic machine-global asset left here: the `/resolve-copilot` command. The `worktree` skill, the `prune-*` scripts, the hooks and the other fleet scripts live in the private `emirers` repo since 2026-10-06 (luvita-docs ADR 0003) and are installed by its `install.sh`. |
| [`scripts/install-workflow.sh`](scripts/install-workflow.sh) | Stamps the per-project workflow skills (`issue-start`, `pr-open`) into a repo, substituting placeholders. |
| [`scripts/install-global-workflow.sh`](scripts/install-global-workflow.sh) | One-time-per-machine: installs the `/resolve-copilot` command. Everything else it used to install now comes from `emirers/install.sh`. |
| [`scripts/setup-project-board.sh`](scripts/setup-project-board.sh) | Idempotent script that ensures a GitHub Project (v2) board has the standard fields. |
| [`workflows/resolve-copilot-comments.yml`](workflows/resolve-copilot-comments.yml) | Canonical "Resolve Copilot review comments" GitHub Actions workflow. When Copilot reviews a PR, Claude applies the valid fixes, pushes them, and resolves the threads. |
| [`actions/brand-claim-check/`](actions/brand-claim-check) | Composite GitHub Action + stdlib Python script: greps a built site or a source tree against a per-repo `brand-rules.json` (banned / required patterns, file presence, locale parity) and fails on violations. Its README has the schema and a copy-paste workflow. Unit-tested by `.github/workflows/actions-test.yml`. |
| [`scripts/install-copilot-workflow.sh`](scripts/install-copilot-workflow.sh) | Copies the Copilot-resolve workflow into a repo's `.github/workflows/`, filling in the name of that repo's PR check workflow. Idempotent. |
| [`workflows/claude-pr-review.yml`](workflows/claude-pr-review.yml) | Canonical "Claude PR review" workflow: reviews every same-repo PR with `claude-code-action`, authenticated with the Max subscription (`CLAUDE_CODE_OAUTH_TOKEN`). Advisory, never a required check. Replaces Copilot review. |
| [`scripts/install-claude-review-workflow.sh`](scripts/install-claude-review-workflow.sh) | Copies the Claude review workflow into a repo's `.github/workflows/claude-review.yml`. Off until the repo sets `CLAUDE_REVIEW_ENABLED=true` and the token secret. Idempotent. |
| [`workflows/bug-close-audit.yml`](workflows/bug-close-audit.yml) | Canonical "Bug close audit" workflow: reopens a bug issue closed without a qualifying commit on `main` in the 7 days after its last reopen. Always on (event-triggered on `issues: closed`), no opt-in switch. |
| [`workflows/bug-needs-test.yml`](workflows/bug-needs-test.yml) | Canonical "Bug test coverage" workflow: a required check ("Bug PRs must add test lines") that blocks a bug-labelled PR with no added test lines, unless it carries `no-test-required`. |
| [`scripts/install-bug-workflows.sh`](scripts/install-bug-workflows.sh) | Copies both bug workflows into a repo's `.github/workflows/`, substituting that repo's issue-key prefix and bug-label name. Idempotent. |

## The contract

Any project that adopts these templates commits to a board with at least these fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `Status` | single-select | Backlog → Todo → In Progress → In Review → Done (+ Blocked) |
| `Priority` | single-select | Urgent / High / Medium / Low |
| `Estimate` | number | Fibonacci story points (0, 1, 2, 3, 5, 8, 13) |
| `Model & Effort` | text | `Model · tier (reason)`, e.g., `Sonnet 5.5 · medium (routine endpoint)`; current models Opus 5.5 / Sonnet 5.5 / Haiku 4.5 / Fable 5.1, tiers per the global CLAUDE.md |
| `Dependent` | text | Readable mirror of the issue's native "Blocked by" links (the source of truth), comma-separated; `#N` for a same-repo blocker, `owner/repo#N` for a cross-repo one, e.g., `#412, other-org/other-repo#420` |

GitHub's native `Parent issue` and `Sub-issues progress` fields are also part of the workflow but exist on every project board by default — no setup needed.

The script is **idempotent and non-destructive**. If a field already exists, it's left alone — including its options. Projects that prefer `P0/P1/P2` over `Urgent/High/Medium/Low` (etc.) keep their local taste; the contract is just that the field exists.

## Git workflow (worktrees + auto-cleanup)

Every project uses the same trunk-based, worktree-isolated flow so multiple agents
never collide on one working tree. It's split into a **global** layer (installed
once per machine) and a **per-project** layer (scaffolded into each repo):

| Layer | Asset | Where it lives | Applies to |
| --- | --- | --- | --- |
| Global | `worktree` skill | `~/.claude/skills/worktree/` | every project |
| Global | `/resolve-copilot` command | `~/.claude/commands/resolve-copilot.md` | every project |
| Global | auto-prune hook (`prune-current-worktrees.sh`) | `~/.claude/settings.json` `SessionStart` | every project |
| Per-project | `issue-start`, `pr-open` skills | `<repo>/.claude/skills/` | that repo |
| Per-project | Workflows + Agent Workflow sections | `<repo>/CLAUDE.md` | that repo |

The **global** layer means a merged worktree is cleaned up automatically the next
time you open *any* repo — no per-project wiring. The **per-project** skills carry
the values that genuinely differ (board number, branch/commit prefix, required CI checks).

### One-time global setup (per machine)

```bash
(cd ~/Projects/emirers && ./install.sh)   # worktree skill, prune scripts, SessionStart auto-prune hook, guards
./scripts/install-global-workflow.sh      # the /resolve-copilot command
```

Both are idempotent. The fleet layer (worktree skill, prune scripts, hooks)
lives in the private `emirers` repo since 2026-10-06 (luvita-docs ADR 0003);
edit it there and re-run its `install.sh`. The only global asset kept here is
the `/resolve-copilot` command under [`global/commands/`](global/commands).

## Copilot review auto-resolve (all repos)

Every repo gets the **"Resolve Copilot review comments"** workflow
([`workflows/resolve-copilot-comments.yml`](workflows/resolve-copilot-comments.yml)).
When GitHub Copilot (`copilot-pull-request-reviewer[bot]`) reviews a PR, Claude runs
in CI, applies the valid suggestions, pushes the fixes to the PR branch, and resolves
the threads it addressed — so nobody has to hand-resolve Copilot's comments each session.

While the workflow is dormant, or for a one-off pass, the global `/resolve-copilot`
command ([`global/commands/resolve-copilot.md`](global/commands/resolve-copilot.md),
installed by `install-global-workflow.sh`) does the same job locally. The two share
the thread query, the reply and resolve mutations, and the fixed / declined / left-open
rule; edit both together.

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

**The workflow is off until a repo opts in — and off means free.** `find-prs` is gated
on a repository variable in its job-level `if:`, which GitHub evaluates before a runner
is allocated. Until the variable is set, the `workflow_run` and cron triggers are skipped
and bill no Actions minutes. To enable a repo, set the variable **and** the API key:

```bash
gh variable set COPILOT_RESOLVE_ENABLED --body true --repo AnunnakiCosmoCrew/<repo>
gh secret set ANTHROPIC_API_KEY --repo AnunnakiCosmoCrew/<repo>
```

The key has to be a *repository* secret: on the org's GitHub Free plan an *organization*
secret does not reach a *private* repo. With the variable on and the key missing,
`find-prs` logs a warning and outputs no PRs, so the Claude job is skipped instead of
failing. The key bills the Anthropic **API** account, not the Claude subscription.
Decision 2026-09-25: leave both unset and the workflow dormant.

Why a variable and not just the missing key: the key can only be checked inside a step
(the `secrets` context is unavailable in a job-level `if:`), and a step only runs once a
runner minute is already being billed. Before this gate, a dormant copy still started a
runner on every PR check completion and every 3 hours, in every repo that carried it.
Copies installed before 2026-10-01 do not have the gate; those were switched off with
`gh workflow disable` instead. Re-run the installer to pick the gate up, then
`gh workflow enable resolve-copilot-comments.yml --repo <owner>/<repo>`.

> **Don't set the key at the org level.** An org secret with visibility `all` *does* reach a
> public repo. The org had such an `ANTHROPIC_API_KEY` (set 2026-07-01); it was deleted on
> 2026-09-25, and no repo has a repository-level one, so the workflow is dormant org-wide.

**Install it into a repo** (idempotent — re-run to roll template updates forward). The
second argument is the `name:` of that repo's PR check workflow, which differs per repo:

```bash
./scripts/install-copilot-workflow.sh ~/Projects/Pelerin "PR Quality & Security Checks"
./scripts/install-copilot-workflow.sh ~/Projects/Pelerin-web "Build"
```

The canonical file carries a `{{PR_CHECK_WORKFLOW}}` placeholder the script fills in.
Leave the name out and the script reuses the one in an already-installed copy, or picks
the repo's only `pull_request` workflow. If there are several, it lists them and stops.

## Bug workflows: close audit + test coverage (code repos)

Two workflows, ported from `WordPower-app` (the first repo to carry them) and
parameterized here so every code repo can install its own copy:

- **[`bug-close-audit.yml`](workflows/bug-close-audit.yml)** reopens a
  bug-labelled issue that was closed without evidence a fix landed: if it was
  reopened in the last 7 days and no commit on `main` since that reopen
  references it (`#N` or `<PREFIX>-N`), the close is reverted with an
  explanatory comment. Enforces "a linked PR is not proof of a fix" (global
  CLAUDE.md). Event-triggered (`issues: closed`), no opt-in switch, no cost
  until a bug issue is actually closed.
- **[`bug-needs-test.yml`](workflows/bug-needs-test.yml)** is a required
  check, "Bug PRs must add test lines": blocks merge of a bug-labelled PR
  that adds no lines under common test paths/conventions, unless the PR
  carries `no-test-required` (leave a comment explaining why when you apply
  it). Event-triggered (`pull_request`); the workflow always starts so a
  required check can't block merge by omission, but the job skips itself
  (no runner, no billed minute) unless the PR carries the bug label and not
  `no-test-required`, and ignores label events for any other label.

Both carry `{{ISSUE_KEY_PREFIX}}` / `{{BUG_LABEL}}` placeholders, substituted
at install time:

```bash
./scripts/install-bug-workflows.sh ~/Projects/Pelerin PEL bug
```

Check the repo's existing labels first (`gh label list --repo <owner>/<repo>`)
— most repos already have a `bug` label; create `no-test-required` if it
doesn't exist yet (`gh label create no-test-required --repo <owner>/<repo>`,
installer prints the exact commands). After installing, add `Bug PRs must add
test lines` to the repo's required-checks ruleset.

Respect each repo's `agent_cap` (`emirers/registry.yaml`, default 3) when
rolling this out across the fleet: skip a repo already at or over its
worktree cap rather than exceeding it, and say so instead.

## Bootstrap a new project

```bash
# 0. One-time per machine (if not done already): install the fleet layer (worktree skill, prune hook, guards)
(cd ~/Projects/emirers && ./install.sh)   # private repo; then ./scripts/install-global-workflow.sh for /resolve-copilot

# 1. Create the repo and project board (manually or via gh repo create + gh project create).
#    --add-readme seeds `main`, so the bootstrap PR in step 7 has a base branch.
gh repo create AnunnakiCosmoCrew/new-thing --public --add-readme
gh repo clone AnunnakiCosmoCrew/new-thing && cd new-thing
gh project create --owner AnunnakiCosmoCrew --title "New Thing"   # note the project number

# 2. Ensure standard board fields exist
./scripts/setup-project-board.sh AnunnakiCosmoCrew <project-number>

# 3. Drop the CLAUDE.md template into the new repo
curl -sL https://raw.githubusercontent.com/AnunnakiCosmoCrew/project-templates/main/CLAUDE.template.md \
  -o CLAUDE.md

# 4. Open CLAUDE.md, replace every {{PLACEHOLDER}}, delete the <!-- OPTIONAL --> blocks
#    you don't need, and fill in the <!-- FILL --> sections with your stack's
#    actual commands.

# 5. Scaffold the per-project workflow skills (issue-start, pr-open) into the repo:
/path/to/project-templates/scripts/install-workflow.sh . \
  --name "New Thing" --prefix NT --branch-prefix feature/nt \
  --worktree-prefix nt --board <project-number> --app-repo new-thing
#    Then fill the <!-- FILL --> required-checks list in .claude/skills/pr-open/SKILL.md.

# 6. Add the Copilot review auto-resolve workflow (from this repo's checkout), naming
#    the new repo's PR check workflow. It stays off, and costs no Actions minutes,
#    until the repo sets COPILOT_RESOLVE_ENABLED=true and ANTHROPIC_API_KEY (see above).
/path/to/project-templates/scripts/install-copilot-workflow.sh . "<PR check workflow name>"

# 7. Add the repo's row to emirers/registry.yaml (kind, board, key, branch, worktree,
#    required_checks) and apply the org-standard main-protection ruleset from it
#    (emirers/scripts/apply-rulesets.sh). Code and site repos take PRs only; git-guard
#    refuses a push to main there, so the bootstrap lands as the repo's first PR:
#    The branch follows the repo's own convention ({branch-prefix}-{issue N}-{slug}), so open
#    the bootstrap issue first (the first issue of a fresh repo is #1) and use its number.
gh issue create --title "Bootstrap CLAUDE.md and workflow skills" --body "Adopt project-templates."
git checkout -b feature/nt-1-bootstrap
git add CLAUDE.md .claude/skills .github/workflows/resolve-copilot-comments.yml
git commit -m "NT-1 chore: add CLAUDE.md, workflow skills + Copilot-resolve workflow (from project-templates)"
git push -u origin feature/nt-1-bootstrap
gh pr create --title "NT-1 chore: bootstrap workflow files" --body "Closes #1" --reviewer @copilot
```

## Maintaining the templates

When the conventions evolve (new field, new workflow step, etc.):

1. Update the relevant source here: `CLAUDE.template.md`, `skill-templates/`, `global/`, `workflows/resolve-copilot-comments.yml`, or `scripts/`.
2. Note the change in this README under "Version history" below.
3. Roll it forward:
   - **Global layer**: the `/resolve-copilot` command is here (`global/commands/`): re-run `./scripts/install-global-workflow.sh`. The worktree skill, prune scripts and hooks are in `emirers`: change them there and run its `install.sh`.
   - **Per-project layer** (`CLAUDE.template.md`, `skill-templates/`): open a PR in each adopting project. These are not auto-applied.
   - **Copilot workflow**: re-run `./scripts/install-copilot-workflow.sh <repo-dir>` against each adopting repo (pass the PR check workflow name the first time) and open a PR with the result.

## Adopting projects

The first adopters, kept as history. By 2026-10 about twenty org repos carry the rendered template; the full list with each repo's board, prefixes and required checks is `emirers/registry.yaml` (private).

| Project | CLAUDE.md | Board | Adopted |
| --- | --- | --- | --- |
| WordPower | [`WordPower-app/CLAUDE.md`](https://github.com/AnunnakiCosmoCrew/WordPower-app/blob/main/CLAUDE.md) | [#11](https://github.com/orgs/AnunnakiCosmoCrew/projects/11) | reference implementation |
| SliceFocus (BE) | [`SliceFocus/CLAUDE.md`](https://github.com/AnunnakiCosmoCrew/SliceFocus/blob/main/CLAUDE.md) | [#8](https://github.com/orgs/AnunnakiCosmoCrew/projects/8) | 2026-06-27 (worktree workflow) |
| SliceFocusFE | [`SliceFocusFE/CLAUDE.md`](https://github.com/AnunnakiCosmoCrew/SliceFocusFE/blob/main/CLAUDE.md) | [#8](https://github.com/orgs/AnunnakiCosmoCrew/projects/8) | 2026-06-27 (worktree workflow) |
| Magpie | [`magpie-app-private/CLAUDE.md`](https://github.com/AnunnakiCosmoCrew/magpie-app-private/blob/main/CLAUDE.md) | [#12](https://github.com/orgs/AnunnakiCosmoCrew/projects/12) | 2026-05-12 |

## Version history

- **2026-10-08** — `bug-needs-test.yml` skips its job (job-level `if:`) on non-bug PRs and on `labeled` / `unlabeled` events for unrelated labels, so they no longer start a billed runner ([#32](https://github.com/AnunnakiCosmoCrew/project-templates/issues/32)). Re-run `install-bug-workflows.sh` in each consumer to pick it up.
- **2026-10-07** — Added `bug-close-audit.yml` and `bug-needs-test.yml` as canonical workflows (W8, [#27](https://github.com/AnunnakiCosmoCrew/project-templates/issues/27)), ported from `WordPower-app` — the only repo enforcing "a linked PR is not proof of a fix" and "red reproducer before green fix" in CI, despite both rules being stated in ten `CLAUDE.md` files. `bug-needs-test.yml`'s Flutter/Gradle test paths became ecosystem-generic globs; both workflows' bug-label and issue-key-prefix are now `{{BUG_LABEL}}` / `{{ISSUE_KEY_PREFIX}}` placeholders, substituted by the new `install-bug-workflows.sh`, same approach as `{{PR_CHECK_WORKFLOW}}`. Added `scripts/test-install-bug-workflows.sh` and a new `actions-test.yml` CI workflow to run it (no `actionlint` yet — not previously used in this repo).
- **2026-10-07** — Brought the templates in line with how the org works now. The contract names the real barriers: the `main-protection` ruleset (PR required, threads resolved, linear history, required checks) and the `git-guard.py` hook from `emirers`, installed through managed settings. Native "Blocked by" links are the source of truth for dependencies, `Dependent` is only a readable mirror (`#N` same-repo, `owner/repo#N` cross-repo), and `issue-start` now looks the blockers up before it touches the board and stops on an open one. `Model & Effort` uses the `Model · tier (reason)` format with current models. `pr-open` documents the merge safeguards. The fresh-repo bootstrap seeds `main` (`--add-readme`), clones, and opens the bootstrap PR from a branch that follows the repo's own prefix and issue-number convention. The `setup-project-board.sh` header was updated to match. Raised by Copilot review on #14.
- **2026-10-06** — The machine-global layer moved to the private `emirers` repo (luvita-docs ADR 0003): `global/scripts/prune-*.sh` and `global/skills/worktree` are removed from here because the installed copies had moved on (merged-PR proof, harness worktree grace) and re-running the installer would have downgraded them; `install-global-workflow.sh` now installs only `/resolve-copilot`. This repo is public, and the fleet scripts know the portfolio.
- **2026-10-04** — Tightened the Copilot-resolve instructions after a review of 22 local `/resolve-copilot` runs. The command now lives here under `global/commands/` and is installed by `install-global-workflow.sh`. The workflow prompt gets the same steps. The runs handled Copilot's points well but improvised the rest. They used three different reply APIs, five of which errored (string IDs, `gh api --repo`, GraphQL built by interpolation). They piped `git push` through `tail`, which hides a rejected push. They held the reply and resolve behind long builds or CI until the user re-ran the command. They checked out PR branches in main clones. The command's "ignore outdated" rule would have skipped live threads. Both now carry: one paginated GraphQL thread query (outdated threads included, review-body findings checked); reply and resolve mutations that take variables, joined by `&&` so a failed reply never resolves; a fixed / declined / left-open rule for what to reply and resolve; and an unpiped push, verified against `@{u}`. The command also works in the branch's worktree, runs only the checks that cover the changed files, and never waits on CI. The workflow still works only threads with no reply yet, matching what its scan triggers on, so it never replies twice to a thread an earlier run left open. It now passes the owner and the bare repository name separately to GraphQL. It does not start for findings that sit only in a review body; those are left to a local `/resolve-copilot` pass. The workflow's trust boundary is unchanged: still no build or tests, still only `gh` and `git`.
- **2026-10-03** — Fixed the `find-prs` scan never matching. It compared the first comment author of each review thread with `copilot-pull-request-reviewer[bot]`, but GraphQL returns that login **without** `[bot]` (the suffix only appears in the REST API and the UI; verified on AnunnakiCosmoCrew/divan PR #19), so once a repo opted in (`COPILOT_RESOLVE_ENABLED` + `ANTHROPIC_API_KEY`) no PR was ever picked up. The recheck stage already used the GraphQL form. Both jq filters now use `copilot-pull-request-reviewer`; the `[bot]` form stays only in the prompt text, which sends Claude to the REST API. Found by Copilot's own review of the divan copy. Copies that predate the fix are re-synced by re-running the installer, per repo.
- **2026-10-01** — A dormant copy no longer bills Actions minutes. `find-prs` is gated on the repository variable `COPILOT_RESOLVE_ENABLED` in its job-level `if:`, which GitHub evaluates before a runner starts, so the `workflow_run` and cron triggers are skipped for a repo that has not opted in (`workflow_dispatch` bypasses the gate for manual debugging). Before this, every trigger started a runner only to find `ANTHROPIC_API_KEY` missing. Enabling a repo now takes the variable **and** the repository secret; the installer's closing hint and the section above say so. Rollout: the copies already in the org repos predate the gate and were switched off the same day with `gh workflow disable`; a repo picks the gate up when the installer is re-run there, followed by `gh workflow enable resolve-copilot-comments.yml`.
- **2026-09-25** — Ported Pelerin's fix for the Copilot-resolve trigger ([AnunnakiCosmoCrew/Pelerin#129](https://github.com/AnunnakiCosmoCrew/Pelerin/pull/129), then [#148](https://github.com/AnunnakiCosmoCrew/Pelerin/pull/148)): `pull_request_review` never ran (GitHub gates the Copilot bot's runs as `action_required`), so the workflow now runs on `workflow_run` of the repo's PR check workflow, with a sparse `0 */3 * * *` cron fallback and `workflow_dispatch`. A `find-prs` job picks the PRs to process, and skips with a warning when `ANTHROPIC_API_KEY` isn't visible. The PR check workflow's name is a `{{PR_CHECK_WORKFLOW}}` placeholder that `install-copilot-workflow.sh` fills in per repo. The trust boundary from the previous entry is kept; Pelerin's copy doesn't have it. Corrected the docs: the key is an optional **repository** secret, because an org secret doesn't reach private repos on GitHub Free. It does reach public repos, so the org-level `ANTHROPIC_API_KEY` (visibility `all`) was deleted the same day, and this repo's own dogfooded copy is removed rather than kept in sync.
- **2026-09-22** — Closed the privileged-execution hole the first pass left open: the workflow no longer asks Claude to run the project's build/tests/lint (that was PR-authored code executing in a job that holds a write-capable token and the org `ANTHROPIC_API_KEY`), and `--allowedTools` now grants only `gh` and `git` instead of blanket `Bash`. Verification moves to the repo's own CI, which runs on the pushed commit and gates the merge anyway. Added a TRUST BOUNDARY comment to the workflow recording why the fork-PR check is necessary but not sufficient. Raised by Copilot review on #3.
- **2026-09-22** — Hardened `workflows/resolve-copilot-comments.yml`: SHA-pinned `anthropics/claude-code-action` (was a floating `@v1` tag), added a per-PR `concurrency` guard, restored the fork-PR safety check the header comment already claimed (`head.repo.full_name == github.repository`), bumped `actions/checkout` to v7, and added explicit `persist-credentials`/`GH_TOKEN`. Picked by auditing the 6 variants the file had already drifted into across 38 adopting repos and choosing the most complete, most recently maintained one (Pelerin's). Re-syncing already-adopting repos is a separate follow-up.
- **2026-07-01** — Added the standard **"Resolve Copilot review comments"** GitHub Actions workflow (`workflows/resolve-copilot-comments.yml`) + `install-copilot-workflow.sh`, and rolled it out to all org repos via PRs. Needs a one-time org-level `ANTHROPIC_API_KEY` secret.
- **2026-10-01** — Landed the 2026-06-27 git-workflow templates (they had been sitting uncommitted in a working copy), together with the changes made to the installed copies since: `prune-current-worktrees.sh` no longer blocks session start (bounded stdin read, background delegate; 2026-07-02), the `worktree` skill's parent path is `~/Projects`, and `setup-project-board.sh` emits raw `jq` output for single-select options.
- **2026-06-27** — Git workflow templatized. Added the global `worktree` skill + universal `SessionStart` auto-prune (`global/`, `install-global-workflow.sh`), parameterized `issue-start`/`pr-open` skill templates (`skill-templates/`, `install-workflow.sh`), and a Workflows routing table + slimmed Agent Workflow section in `CLAUDE.template.md`. SliceFocus (BE + FE) retrofitted to match WordPower; the per-repo `wp-worktree`/`sf-worktree` skills were replaced by the single global `worktree` skill.
- **2026-05-12** — Initial templates. CLAUDE.md skeleton extracted from WordPower-app/CLAUDE.md after WP-565 (added `Dependent` field workflow, closed WP-29 staleness). `setup-project-board.sh` ensures Status, Priority, Estimate, Model & Effort, Dependent fields exist.
