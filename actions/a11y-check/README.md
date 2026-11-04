# a11y-check

One reusable CI check for every site and web app: a composite GitHub Action (plus one
standard-library Python script) that serves a built `dist/` or a plain-HTML repo root on a
local port, runs axe-core on each page, and **fails the job on any serious or critical
violation** at WCAG 2.2 A/AA (the level of [luvita-docs ADR 0011](https://github.com/AnunnakiCosmoCrew/luvita-docs/blob/main/adr/0011-front-end-platform-and-accessibility-baseline.md) §5.1). Each violation is printed with its
page, impact, rule, selector, help text and help URL.

Automated checks find about half of accessibility problems; this does not replace the manual
keyboard and screen-reader pass the ADR requires per release.

- Script: [`a11y_check.py`](a11y_check.py), Python 3.8+, no dependencies.
- Action: [`action.yml`](action.yml).
- Tests: [`tests/`](tests), run with `python3 -m unittest discover -s actions/a11y-check/tests`.

## Use it

After the build step, in the repo's PR workflow (the runner needs Chrome; `ubuntu-latest` has it):

```yaml
      - name: Accessibility check
        uses: AnunnakiCosmoCrew/project-templates/actions/a11y-check@main
        with:
          root: dist          # a built site; use "." for a plain-HTML repo
```

Then **add that job to the repo's ruleset required checks** (`main-protection`), or it is
advisory only. Pin `@main` to a commit SHA if the repo wants a frozen copy.

| Input | Default | Meaning |
| --- | --- | --- |
| `root` | `.` | Directory to serve. |
| `urls` | all `.html` under root | Paths to test, one per line or comma separated (`/`, `docs/` map to `index.html`). |
| `allowlist` | `.a11y-allow.json` | Allow-list file, looked up inside `root` first, then the workspace. Missing means no exceptions. |
| `standard` | `wcag22aa` | `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa` or `wcag22aa`; sets the axe rule tags. |
| `python` | `python3` | Interpreter. |

Outputs: `pages`, `violations` (blocking, allow-list applied), `allowed`.

Exit status: 0 clean, 1 violations, 2 the check could not run (no pages, bad allow-list, axe
or the browser failed). A broken tool never reads as a pass.

Moderate and minor findings are not blocking and not printed; only serious and critical are.

## Allow-list

For a documented exception, e.g. a third-party widget you cannot change:

```json
{
  "allow": [
    {
      "rule": "color-contrast",
      "selector": ".cookie-banner *",
      "reason": "Third-party consent widget; vendor ticket ACME-123 open",
      "page": "index.html"
    }
  ]
}
```

- `rule` is the axe rule id, `selector` the CSS selector axe prints (shadow-DOM paths joined by
  a space). `selector` and the optional `page` accept `*` and `?` wildcards only (brackets are literal, so `input[type="email"]` works).
- **An entry with an empty or missing `reason` fails the run** (exit 2). A reason is the point of
  the list.
- An entry that matches nothing prints a warning so stale exceptions get removed.

## Why `@axe-core/cli`, pinned at 4.14.0

Chosen over `pa11y-ci`: pa11y's axe runner cannot select WCAG 2.2 rules (it hard-codes the
2.0/2.1 tags plus `best-practice`) and filters by rule id only, while `axe --tags` takes
`wcag22aa` directly and its JSON carries impact and per-node selectors, which the
selector-level allow-list needs. The version is pinned because the rule set ships inside
axe-core, so an unpinned run could start failing with no change to the site. Bump it
deliberately, with the fixtures in the same PR.

On GitHub-hosted runners the script passes the runner's own chromedriver (`CHROMEWEBDRIVER`) so
the driver matches the installed Chrome; elsewhere the driver bundled with the CLI is used and
must match your Chrome (or install one with `npx browser-driver-manager`).
