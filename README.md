# project-templates

Templates and bootstrap tooling for new AnunnakiCosmoCrew projects. Apply these to a fresh repo + project board to get a working CLAUDE.md and a project board with the standard fields in under a minute.

## What's here

| File | What it does |
| --- | --- |
| [`CLAUDE.template.md`](CLAUDE.template.md) | Parameterized CLAUDE.md skeleton. Copy → fill placeholders → drop into the new repo as `CLAUDE.md`. |
| [`scripts/setup-project-board.sh`](scripts/setup-project-board.sh) | Idempotent script that ensures a GitHub Project (v2) board has the standard fields. |

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

# 5. Commit and push.
git add CLAUDE.md
git commit -m "chore: add CLAUDE.md (from project-templates)"
git push
```

## Maintaining the templates

When the conventions evolve (new field, new workflow step, etc.):

1. Update `CLAUDE.template.md` and / or `scripts/setup-project-board.sh` here.
2. Note the change in this README under "Version history" below.
3. Open a PR in each adopting project to roll the change forward — the templates are not auto-applied to existing projects.

## Adopting projects

| Project | CLAUDE.md | Board | Adopted |
| --- | --- | --- | --- |
| WordPower | [`WordPower-app/CLAUDE.md`](https://github.com/AnunnakiCosmoCrew/WordPower-app/blob/main/CLAUDE.md) | [#11](https://github.com/orgs/AnunnakiCosmoCrew/projects/11) | reference implementation |
| Magpie | [`magpie-app-private/CLAUDE.md`](https://github.com/AnunnakiCosmoCrew/magpie-app-private/blob/main/CLAUDE.md) | [#12](https://github.com/orgs/AnunnakiCosmoCrew/projects/12) | 2026-05-12 |

## Version history

- **2026-05-12** — Initial templates. CLAUDE.md skeleton extracted from WordPower-app/CLAUDE.md after WP-565 (added `Dependent` field workflow, closed WP-29 staleness). `setup-project-board.sh` ensures Status, Priority, Estimate, Model & Effort, Dependent fields exist.
