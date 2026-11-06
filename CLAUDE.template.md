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
  {{WORKTREE_PREFIX}}         sibling worktree dir prefix, e.g., "wp", "sf-be", "sf-fe"
  {{COMMIT_PREFIX_EXAMPLE}}   e.g., "WP-42", "MAG-7"
  {{TECH_STACK_DESCRIPTION}}  one-paragraph stack summary
  {{A11Y_SURFACE_AND_STANDARD}} / {{A11Y_AUTOMATED_CHECK}} / {{A11Y_MANUAL_PASS}} / {{A11Y_TOKEN_FILE}} / {{A11Y_LAST_MANUAL_PASS_DATE}}
                              optional: omit all five with the Accessibility section (ADR 0011 §5.1);
                              see the FILL comments there.
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

## Workflows

Procedural how-tos live in skills that load on demand. Pick the flow that matches the work.

| Flow              | When to use                                              | Skill                          |
| ----------------- | -------------------------------------------------------- | ------------------------------ |
| **Issue start**   | Beginning work on any tracked GitHub issue               | `issue-start` (this repo)      |
| **Worktree mgmt** | Creating or cleaning up a worktree                       | `worktree` (global, all repos) |
| **Open PR**       | After pushing a feature branch                           | `pr-open` (this repo)          |
| **Direct edit**   | Trivial changes: typos, dep bumps, one-line config, docs | None — just commit (from a worktree) |

`issue-start` and `pr-open` are scaffolded into `.claude/skills/` by
`project-templates/scripts/install-workflow.sh`. The `worktree` skill is global
(`~/.claude/skills/worktree/`, installed from the private `emirers` repo), shared by every project.

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

1. **Add issue to the project board** when creating via `gh issue create` (it does NOT auto-add). Use `gh project item-add {{PROJECT_BOARD_NUMBER}} --owner {{REPO_OWNER}} --url <issue-url>`. Then set board fields: `Status`, `Priority`, `Estimate`, `Model & Effort`, and `Dependent` (if applicable — see "Dependent vs. sub-issues" below). The issue body starts with a `## In short` block (luvita-docs ADR 0005, amendment 2): `- **Why:**` (the problem as an outcome: who is hurt, what it costs), `- **What:**` (what is different when it is done), `- **How:**` (the approach, one sentence); about 60 words for a reader who knows the product but not the code, so no file paths, function or flag names, or bare issue numbers, and internal names explained the first time. Below it the body carries a `## Premise check` block (second section in `ISSUE_TEMPLATE/task.md`) that you write yourself (luvita-docs ADR 0005, amendment 1): `- Observed problem:`, `- Evidence it exists:` (a link, log line, metric or test you looked at, or `assumed`), `- Cost of doing nothing:`, `- What would show this issue was wrong:`; an agent's first line is `_Written by an agent (<session or PR link>); the founder's move to Todo signs it off._` Without it the issue is never dispatched.
2. **Set an estimate** (Fibonacci: 0, 1, 2, 3, 5, 8, 13) on the project board. Bugs are `0`.
3. **Set the `Model & Effort`** on the project board: format, model names and tiers per the global CLAUDE.md.
4. **Record dependencies** as native GitHub "Blocked by" links (REST `POST /repos/{owner}/{repo}/issues/{n}/dependencies/blocked_by` with `-F issue_id=<db id>`; cross-repo works) and mirror them in `Dependent` as a comma-separated list: `#N` for a same-repo blocker, `owner/repo#N` for a cross-repo one (e.g., `#412, other-org/other-repo#420`). An issue with an open blocker is `Blocked`, never `Todo`.
5. **Move ticket to "In Progress"** on the project board before writing any code.
6. **Create a feature branch** from latest `main`: `{{BRANCH_PREFIX}}-{N}-{slug}`.
7. **Implement and verify**: run the commands from "Build / Test / Lint Commands" above. All must pass before pushing.
8. **Commit** to the feature branch with a descriptive message referencing the issue number.
9. **Push and open a PR** with `Closes #NNN` in the body so the issue auto-closes on merge.

> **Do NOT skip steps 1–5.** The project board must reflect the current state of work at all times.

### Dependent vs. sub-issues

The board exposes two related fields for capturing how issues relate to each other. Choose deliberately:

- **Native "Blocked by"** (source of truth) **+ `Dependent`** (text field, a readable mirror). Use when this issue is *blocked by* one or more **peer** issues — same scope tier, not nested. Mirror value: a comma-separated list of issue references, `#N` for a same-repo blocker and `owner/repo#N` for a cross-repo one, e.g., `#412, other-org/other-repo#420`. Read as "this is dependent on those". Update or clear both as blockers resolve; when closing an issue, move dependents whose blockers are all closed from `Blocked` to `Todo`.
- **`Parent issue` + `Sub-issues progress`** (GitHub-native sub-issues). Use when this issue is one *step inside* a larger one. The parent is the umbrella, the children are the decomposition. Progress on the parent updates automatically as children close.

**Heuristic:** if one issue can't start until another finishes but they aren't parts of the same larger thing, use `Dependent`. If they're slices of the same larger thing, use sub-issues. The two are not mutually exclusive — a child of one parent can also be `Dependent` on an unrelated peer.

### Bug Fixes — Test-Driven Bug Fixing (TDBF)

When fixing a bug, the failing test that reproduces it must be written and committed *before* the fix. Two commits on the same branch:

1. **Red commit** — test that reproduces the bug (test will fail by design; lint/analyze must still pass). Commit: `{{ISSUE_PREFIX}}-{N} test: reproduce <bug description>`.
2. **Green commit** — the fix. All tests pass. Commit: `{{ISSUE_PREFIX}}-{N} fix(<scope>): <what the fix does>`.

### Branch Protection

- `main` is protected by the org-standard `main-protection` ruleset (code and site repos): pull request required, every review thread resolved (reply **and** explicitly resolve), linear history, no force-push or deletion. Repo settings: squash merge only, auto-delete head branches. The ruleset is applied from the repo's row in `emirers/registry.yaml`; add the row when the repo is created.
- Locally, `git-guard.py` (Claude Code managed settings, from the private `emirers` repo) refuses `gh pr merge --admin`, a push to `main` in a code repo, blanket staging (`git add -A`/`.`, `git commit -a`), and a merge while the PR is a draft, a check is red or pending, or a thread is unresolved. Details: `emirers/README.md`.

<!-- OPTIONAL: required-status-checks. Enable once your CI is stable; until
     then, delete this bullet so you can merge without ghost-blocking checks.
     The list lives in the ruleset and in emirers/registry.yaml `required_checks`;
     change both together. -->
- **Required status checks** — a PR will not merge until ALL of:
  - <!-- FILL: e.g., `Build and test` (Backend CI) -->
  - <!-- FILL: e.g., `Analyze, format, test` (Frontend CI) -->
  - <!-- FILL: e.g., `Static analysis` (Semgrep SAST) -->
<!-- /OPTIONAL -->

<!-- OPTIONAL: Claude review. Delete this whole section if the Claude PR
     review workflow isn't installed on this repo yet
     (project-templates/scripts/install-claude-review-workflow.sh). -->
### Claude Code Review

Every new non-draft PR is reviewed by the Claude PR review workflow (`.github/workflows/claude-review.yml`, Max OAuth token). It leaves inline comments, often with one-click suggestion blocks, and ends with one comment-only summary review. Treat it like a human review:

- **Any thread Claude opens must be addressed**: reply with the fix (or why no change is needed) **and** explicitly resolve the thread. `/resolve-copilot` handles Claude's threads too.
- The `main-protection` ruleset blocks the merge until every review thread is resolved, and `git-guard.py` refuses `gh pr merge` while one is open.
- Claude judges the change against this `CLAUDE.md`; keep it current when conventions change.
- **Draft-first PRs:** a draft is not reviewed automatically. Add the `claude-review` label to review it as a draft (`gh pr edit <N> --add-label claude-review`), resolve the threads, push once, then `gh pr ready`. A labelled PR is not reviewed again when it is marked ready.
- The review runs once per PR, not per push. To get a fresh review (or one on a PR opened before the workflow existed), add the `claude-review` label. Never add a polling or nudge cron for it.
<!-- /OPTIONAL -->

## Accessibility

Standard and check follow luvita-docs ADR 0011 §5.1. Delete this section if the repo renders nothing a person uses.

- **Row of the table this repo follows:** {{A11Y_ROW}} (browser/web view: WCAG 2.2 AA; Flutter iOS/macOS: Apple HIG; Flutter Android: Material 3; Tauri shell: macOS HIG + Windows app design; native macOS: macOS HIG).
- **Automated check (required CI):** {{A11Y_CHECK}} (web: `AnunnakiCosmoCrew/project-templates/actions/a11y-check@main` after the build step, job added to the ruleset's required checks; exceptions live in `.a11y-allow.json`, each with a reason).
- **Last manual pass (screen reader / keyboard walk):** {{A11Y_LAST_MANUAL_PASS}}

## Agent Workflow

Multiple Claude Code agents may work on this repo concurrently. To prevent filesystem conflicts, every agent **must** develop inside a dedicated `git worktree` — never directly in the main working directory.

- **Create / clean up**: use the global `worktree` skill. Branch `{{BRANCH_PREFIX}}-<N>-<slug>`, sibling worktree path `../{{WORKTREE_PREFIX}}-<N>-<slug>`.
- **Auto-cleanup**: `~/.claude/scripts/prune-worktrees.sh` (installed from the private `emirers` repo) runs on every `SessionStart` via `prune-current-worktrees.sh` and removes a worktree only when its tree is clean **and** a merged PR contains its HEAD (or it is already on `main`). Dirty trees, unpushed commits and closed-unmerged PRs are left alone, so commit and push before ending a session. Log: `~/.claude/logs/prune-worktrees.log`.
- **Rules**: one worktree per feature branch; one feature branch per issue; never `.claude/worktrees/` or `.worktrees/`; if you're editing in the root clone, stop and create a worktree first.

## Decision discipline

These rules exist because an implementing agent accepts the premise it is handed and tends to add what was not asked for. They are not about code quality. They are about keeping the founder's decision the only decision in the PR.

1. **Implement only what the issue specifies.** The issue's acceptance criteria are the scope. A "reasonable next step" that is not in the issue is out of scope. If you think it is needed, say so in the PR body under "Unrequested design choices" and leave it out of the diff, or open a new issue in Backlog.

2. **Name every unrequested design choice.** Every choice the issue did not specify (a new class, a new package, a pattern, a library, a changed API shape, a changed default, a schema change) goes in the PR body in a section titled `Unrequested design choices`, placed directly under the existing `Founder check:` line, one bullet each, with the simplest alternative you rejected and why. An empty section reads `Unrequested design choices: none`.

3. **No new abstractions, modules or dependencies without an ADR reference.** A new module, a new layer, a new cross-cutting abstraction, a new runtime dependency or a new build plugin needs an existing ADR that permits it. Cite it as `ADR: adr/NNNN` in the PR body. If no ADR covers it, stop and ask (rule 5). Do not write the ADR yourself inside an implementation PR.

4. **Do not touch the guardrails.** Never edit `archunit.properties`, `src/test/resources/frozen/**`, `config/pmd-tests.xml`, mutation or coverage thresholds in `pom.xml`, or anything under `.github/workflows/` as part of a feature PR. If a guardrail blocks you, that is the signal that the change needs a decision, not a config edit. Ask (rule 5).

5. **Stop and ask when the premise looks wrong.** If, while reading the code, the issue's stated problem does not exist, is already fixed, has a cheaper fix than the one requested, or would require changing something the issue did not mention, do not implement. Push the branch, label the issue `needs-decision`, and post a comment whose first line is `<!-- needs-decision --> @mertyertugrul <one-sentence question>`, followed by what you observed, the options, and your recommended option. Then stop. An issue whose premise is wrong is a decision, not a task.

6. **Never weaken a test to pass.** Do not add `@Disabled`, `@Ignore`, `assumeTrue(false)`, broadened assertions, deleted assertions, lowered thresholds or widened timeouts to make CI green. If a test is wrong, say so under `Not verified` and ask. Keep structural changes (refactoring, renames, moves) and behavioural changes in separate commits, and in separate PRs when both are more than trivial.

7. **State what was verified and what was not.** The PR body ends with two headed lists:
   - `Verified`: each claim with the command you ran and its output, or the test name, or the file and line. "All tests pass" alone is not evidence.
   - `Not verified`: everything you could not run, reproduce, benchmark or test in this environment, including performance claims. If you could not build a reproducer, say so.

8. **Tiering is not yours to lower.** Fill the `Founder check:` line honestly. CI classifies the tier from the diff; your line can raise the tier, never lower it. If you are unsure whether something is `irreversible`, `money`, `public`, `security` or `product`, mark it.

9. **Keep PRs readable in one sitting.** One issue, one PR. If the diff grows past what a reviewer can read in about an hour, split it and say so.

<!-- Rules 4 and 6 use the examples of the Java/Spring Boot repos (archunit.properties, pom.xml, pmd-tests.xml,
     @Disabled, @Ignore). Adapt both lists to this repo's stack: its guardrail files (lint config, frozen
     fixtures, coverage thresholds) and its way of skipping a test. The ban on editing .github/workflows/ applies
     to feature PRs in an adopting repo; a PR whose issue is about the workflows themselves is exempt. -->

<!-- OPTIONAL: delete this section only for a repo with no user interface (a pure API, a docs repo, a CLI). -->
## Accessibility

Canonical text: luvita-docs ADR 0011 §5.1. Every repo with a user interface follows one row of the per-surface table and records it here. Resync this section from `project-templates/CLAUDE.template.md` whenever ADR 0011 changes.

- **Surface and standard** (pick the row of ADR 0011 §5.1 this repo follows): {{A11Y_SURFACE_AND_STANDARD}}
  <!-- FILL, one of:
       Browser or web view (Astro, Vue, React, Tauri panes): WCAG 2.2 Level AA; widget behaviour per WAI-ARIA APG
       Flutter on iOS and macOS: Apple HIG (44x44 pt targets, Dynamic Type, VoiceOver, Reduce Motion)
       Flutter on Android: Material 3 (48x48 dp targets, TalkBack)
       Tauri desktop shell: macOS HIG and Windows app design at the shell level
       Native macOS: macOS HIG
       A repo that spans two surfaces lists both rows. -->
- **Automated check and where it runs**: {{A11Y_AUTOMATED_CHECK}}
  <!-- FILL, e.g. "axe-core on the built pages, job `a11y`, a required check" (HTML);
       "`meetsGuideline` with labeledTapTargetGuideline, textContrastGuideline and the platform tap-target guideline on every screen, in `flutter test`" (Flutter);
       "`XCUIApplication.performAccessibilityAudit()` in the smoke UI tests" (native macOS). -->
- **Manual pass per release**: {{A11Y_MANUAL_PASS}}
  <!-- FILL: the assistive technology (VoiceOver, TalkBack, Narrator, keyboard only) and the main tasks walked. -->
- **Colour token file**: {{A11Y_TOKEN_FILE}} <!-- FILL: path of the one file or package colours are read from (ADR 0011 §5.2), e.g. the vendored build of `cosmocrew-web/packages/design`. -->
- **Last manual pass**: {{A11Y_LAST_MANUAL_PASS_DATE}} <!-- FILL: YYYY-MM-DD, or "never" until the first one is recorded. -->

Definition of Done for any UI change:

- The automated check above is green in required CI. Never silence it with an allow-list entry, a disabled rule or a lowered threshold to get green (rule 6 of Decision discipline); a documented exception is its own reviewed change.
- Text keeps 4.5:1 contrast (3:1 for large text and UI components).
- A release that changes a main task updates **Last manual pass** above, or says in the PR body under `Not verified` that the pass is still owed.

Implementation rules for new UI:

- **Web widgets:** build on headless, APG-conformant primitives (Reka UI for Vue, Radix for React) or this repo's own primitives. Do not hand-roll ARIA for a dialog, menu, combobox, tabs or listbox.
- **Flutter:** build on `material_ui` and `cupertino_ui`, and use the `.adaptive` constructors on Apple platforms (switches, sliders, dialogs, page transitions, icons, scroll physics).
- **No hard-coded colours** outside the colour token file named above.

## Project Management

- **Project board**: GitHub Projects board #{{PROJECT_BOARD_NUMBER}} (`{{REPO_OWNER}}` org)
- **Issue tracking**: GitHub Issues on this repo + the project board
- **Board fields**: `Status`, `Priority`, `Estimate` (Fibonacci 0, 1, 2, 3, 5, 8, 13), `Model & Effort`, `Dependent` (blocking peer issues), `Parent issue` (for sub-issue decomposition)
- **Architecture decisions**: Documented in `{{REPO_OWNER}}/{{DOCS_REPO}}` (drafts) and promoted to `docs/decisions/` here when accepted. Write each ADR from [`ADR.template.md`](https://github.com/AnunnakiCosmoCrew/project-templates/blob/main/ADR.template.md) (evidence, dated metric, alternatives, kill criteria, reversibility; luvita-docs ADR 0006)
