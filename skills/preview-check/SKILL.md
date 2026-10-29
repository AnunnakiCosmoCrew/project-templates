---
name: preview-check
description: Screenshot and smoke-check the pages a UI change touches (mobile and desktop width, console errors, failed requests). Use only after changing visible UI in a web or site repo, such as components, pages, styles or layout. Do not use for backend, config, docs, CI or other non-visual changes.
---

# Preview check

Look at the pages you changed before you open the PR, and say what you saw in the PR body.

## Rules

- Node Playwright only, with the Chromium that is already installed at `/opt/pw-browsers/chromium-*`. Launch it with `executablePath` and `args: ['--no-sandbox']`.
- Never run `playwright install`. The preinstalled browser belongs to a different Playwright version and a fresh download will not be found.
- Do not add Playwright to the repo's dependencies or to any workflow. Use a global or scratchpad install (`NODE_PATH` or `npm i playwright-core --prefix <scratchpad>`).
- Write everything (screenshots, `report.json`, server log) to the session scratchpad, not the repo.

## Steps

1. **List the routes** the diff touches. Map each changed component or page to the route(s) that render it. If you cannot tell, take the home page plus every route in the changed directory.
2. **Start the repo's server yourself**, in the background, from the repo's own scripts (`npm run dev`, `npm run preview` after a build, or the framework's equivalent). If auto mode refuses `npm run dev`, build and serve the output instead (`npm run build`, then the preview or a static server). Wait until the port answers; read the port from the server log, do not assume it. Stop the server when you are done.
3. **Screenshot each route at two widths**: mobile 390 px wide and desktop 1280 px wide, full page, after `networkidle`.
4. **Collect problems** for every route: `console` messages of type `error`, `pageerror` events, and failed requests (`requestfailed`, or responses with status 400 or higher).
5. **Look at the screenshots** (open the PNGs). Check for overflow or horizontal scroll at 390 px, clipped or overlapping text, missing images, and anything that does not match what the change was meant to do.
6. **Report in the PR body**. Images cannot be attached through the API, so describe the result: routes checked, widths, what you looked at, the console and request findings (or "none"), and any defect you fixed or left. Name the scratchpad path only as a note; do not link it.

## Sketch

```js
const { chromium } = require('playwright-core');
const { globSync } = require('node:fs');
const executablePath = globSync('/opt/pw-browsers/chromium-*/chrome-linux/chrome')[0];
const browser = await chromium.launch({ executablePath, args: ['--no-sandbox'] });
for (const [name, width, height] of [['mobile', 390, 844], ['desktop', 1280, 800]]) {
  const page = await (await browser.newContext({ viewport: { width, height } })).newPage();
  const problems = [];
  page.on('console', m => m.type() === 'error' && problems.push(`console: ${m.text()}`));
  page.on('pageerror', e => problems.push(`pageerror: ${e.message}`));
  page.on('requestfailed', r => problems.push(`failed: ${r.url()}`));
  page.on('response', r => r.status() >= 400 && problems.push(`${r.status()}: ${r.url()}`));
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${out}/${slug}-${name}.png`, fullPage: true });
}
await browser.close();
```

Adjust the glob if the Chromium build lays out its binary differently (`ls /opt/pw-browsers/chromium-*`).
