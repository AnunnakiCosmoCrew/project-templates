---
name: Task
about: A unit of work for an agent or a person, with its plain-language summary and premise check
title: ''
labels: ''
assignees: ''
---

## In short
_Three plain lines for the founder reading this cold in six months (luvita-docs ADR 0005, amendment 2). About 60 words; no file paths, function or flag names, or bare issue numbers; explain any internal name the first time. Delete this line._
- **Why:** <the problem as an outcome: who is hurt and what it costs>
- **What:** <what will be different when this is done>
- **How:** <the approach, in one sentence>

## Premise check
_Whoever opens the issue fills this (luvita-docs ADR 0005, amendment 1). An agent replaces this line with `_Written by an agent (<session or PR link>); the founder's move to Todo signs it off._`_
- **Observed problem:** <what happened, where, when; a link or log line if one exists>
- **Evidence it exists:** <link, metric, message, test; or "assumed">
- **Cost of doing nothing:** <one sentence>
- **What would show this issue was wrong:** <one observation that would make me close it unbuilt>

## Scope (planner or founder)
- [ ] Acceptance criteria are listed below as testable statements
- [ ] What is explicitly out of scope is listed
- [ ] The simplest alternative (including "do nothing") is named and the reason it was rejected is one sentence
- [ ] Any new module, abstraction, dependency, schema change or public API change cites an ADR: `ADR: <path to the ADR file, e.g. adr/NNNN or docs/decisions/NNNN>` (or the issue is Blocked until one exists)
- [ ] Tier, if any: irreversible | money | public | security | product

## Verification plan
- [ ] The test or check that proves the acceptance criteria is named (existing test, new test, manual step with expected output)
- [ ] Anything that cannot be verified in CI is listed so the PR can say so under "Not verified"

## Gate
- [ ] Estimate, Priority and Model & Effort are set
- [ ] No open blocker (native Blocked-by links are clear)
- [ ] Founder has read the premise check and moved this to Todo (the sign-off)

## Acceptance criteria
1. ...
2. ...

## Out of scope
- ...
