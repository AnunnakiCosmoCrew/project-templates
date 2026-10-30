---
name: Task
about: A unit of work for an agent or a person, with the founder's premise check
title: ''
labels: ''
assignees: ''
---

## Premise check
_Founder fills this before Status moves to Todo._
- **Observed problem:** <what happened, where, when; a link or log line if one exists>
- **Evidence it exists:** <link, metric, message, test; or "assumed">
- **Cost of doing nothing:** <one sentence>
- **What would show this issue was wrong:** <one observation that would make me close it unbuilt>

## Scope (planner or founder)
- [ ] Acceptance criteria are listed below as testable statements
- [ ] What is explicitly out of scope is listed
- [ ] The simplest alternative (including "do nothing") is named and the reason it was rejected is one sentence
- [ ] Any new module, abstraction, dependency, schema change or public API change cites an ADR: `ADR: adr/NNNN` (or the issue is Blocked until one exists)
- [ ] Tier, if any: irreversible | money | public | security | product

## Verification plan
- [ ] The test or check that proves the acceptance criteria is named (existing test, new test, manual step with expected output)
- [ ] Anything that cannot be verified in CI is listed so the PR can say so under "Not verified"

## Gate
- [ ] Estimate, Priority and Model & Effort are set
- [ ] No open blocker (native Blocked-by links are clear)
- [ ] Founder has moved this to Todo after filling the premise check

## Acceptance criteria
1. ...
2. ...

## Out of scope
- ...
