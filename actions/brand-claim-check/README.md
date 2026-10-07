# brand-claim-check

One reusable CI check for every public surface: a composite GitHub Action (and a
single standard-library Python script) that greps a built site or a source tree
against a JSON rules file of **banned** and **required** patterns, prints every
offending `file:line` together with the rule's reason, and exits 1 on any violation.

It exists because the grep-able brand and claim rules (an attribution line, a
street-address ban, a product name that must never appear, a legal claim that
must never be made) were written down in many `CLAUDE.md` files and checked by
nobody. The script is generic: everything portfolio-specific lives in the
consuming repo's `brand-rules.json`.

- Script: [`brand_check.py`](brand_check.py) — Python 3.8+, no dependencies.
- Action: [`action.yml`](action.yml) — a composite action that runs the script.
- Tests: [`tests/`](tests) — `python3 -m unittest discover -s actions/brand-claim-check/tests`.

## Two ways to consume it

**Vendor the script** (no cross-repo dependency; the first version of every
consumer in the portfolio does this):

```sh
mkdir -p .github/scripts
curl -fsSL https://raw.githubusercontent.com/AnunnakiCosmoCrew/project-templates/main/actions/brand-claim-check/brand_check.py \
  -o .github/scripts/brand-check.py
```

then in the workflow, after the build:

```yaml
      - name: Brand and claim check
        run: python3 .github/scripts/brand-check.py --rules brand-rules.json
```

**Use the action** (keeps consumers on one copy of the script):

```yaml
      - name: Brand and claim check
        uses: AnunnakiCosmoCrew/project-templates/actions/brand-claim-check@main
        with:
          rules: brand-rules.json   # default
          # root: dist              # optional; overrides "root" in the rules file
```

Pin `@main` to a tag or a commit SHA once one exists.

## Copy-paste workflow (static site built with npm)

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - run: npm run build
      - name: Brand and claim check
        run: python3 .github/scripts/brand-check.py --rules brand-rules.json
```

For a docs or code repo with nothing to build, drop the Node steps and point the
rules file's `root` at `.` (or at `site/`).

## The rules file

```jsonc
{
  "root": "dist",                 // scan root, relative to the rules file. Default "."
  "ignore": ["coverage/**"],      // extra ignores; .git/**, node_modules/** are built in
  "rules": [
    {
      "id": "no-street-address",  // unique; appears in every finding
      "kind": "banned",           // banned | required | file-banned | file-required | pair
      "pattern": "yal[ıi]kent|69/25",   // regex (Python re). Case-insensitive unless "flags" says otherwise
      "paths": ["**/*.html"],     // which files the rule applies to (gitignore-style globs)
      "exclude": ["drafts/**"],   // files the rule skips
      "allow": ["\"addressLocality\":\"Bodrum\""],  // exact strings blanked out before a banned regex runs
      "severity": "error",        // error (default, fails the run) | warn (reported only)
      "why": "LUVITA.md: the registered office is the founder's home."   // required
    }
  ]
}
```

### Rule kinds

| kind | meaning | finding |
| --- | --- | --- |
| `banned` | `pattern` must not match anywhere in a file that `paths` selects | one per match, with `file:line` and the matched text |
| `required` | every file that `paths` selects must contain at least one match of `pattern` | one per file without a match |
| `file-banned` | no file may exist at `paths` (e.g. `/CNAME` before a domain is registered) | one per existing file |
| `file-required` | at least one file must exist at `paths` (e.g. `/index.html`) | one per rule |
| `pair` | every file under `left` that `paths` selects has a twin under `right`, and vice versa (locale parity: `left: ""`, `right: "en/"`) | one per missing twin |

### Allow lists

`allow` is a list of **exact strings**. Before a `banned` pattern runs over a
file, each allowed string is blanked out, so a rule like "no *Enerji* outside
the legal block" can coexist with a footer that must contain the full trade
name: allow the full trade name, ban the word. The same trick lets a JSON-LD
`"addressLocality":"Bodrum"` survive a "no city in visible copy" rule.

Prefer `allow` for one-off exact strings and `exclude` for whole files (a
`CLAUDE.md` that *quotes* the forbidden claim in order to forbid it, test
fixtures, frozen historical documents).

### Globs

`.gitignore` semantics: a pattern without `/` matches the basename at any depth
(`*.html`, `CNAME`); a leading `/` anchors it to the scan root (`/index.html`);
`**` spans directories; `*` and `?` never cross `/`.

### Regex notes

- Patterns are compiled with `re.IGNORECASE` by default. Set `"flags": ""` for
  a case-sensitive rule, or any subset of `imsx`.
- Negative lookahead works: `"©\\s*\\d{4}\\s*(?!CosmoCrew)\\S"` bans every
  copyright line whose holder is not CosmoCrew.
- Remember JSON escaping: one backslash in the regex is two in the file.
- Built HTML may carry entities (`&copy;`, `&mdash;`, `&#350;`); write the
  required-pattern regex to accept the entity *and* the literal.

### Severity and the first rollout

When a repo's current content already violates a rule, do not weaken the rule:
set `"severity": "warn"`, so the check reports it without failing the PR, and
list the finding in the PR body for a human to decide. Flip it back to `error`
once the content is fixed.

## Output

Plain text locally, GitHub annotations under `GITHUB_ACTIONS=true` (or
`--format github`):

```
dist/en/about/index.html:41: error: [no-street-address] banned: 'Yalıkent' — LUVITA.md: the registered office is the founder's home.
dist/en/privacy/index.html: error: [attribution] required pattern not found: /…/ — luvita-docs ADR 0001
brand-check: 2 error(s), 0 warning(s)
```

Exit codes: `0` clean (warnings allowed), `1` at least one error finding, `2`
configuration error (bad rules file, missing scan root — usually "build first").

## Running locally

```sh
npm run build                      # if the rules scan dist/
python3 .github/scripts/brand-check.py --rules brand-rules.json
python3 .github/scripts/brand-check.py --rules brand-rules.json --root some/other/dir
```
