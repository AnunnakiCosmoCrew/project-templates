# ADR NNNN: <decision in one line>

- Status: proposed | accepted | superseded by NNNN | reversed on <date>
- Date: YYYY-MM-DD
- Tier: none | irreversible | money | public | security | product   (same tiers as the Founder check line)

## 1. Problem statement
One paragraph. What is wrong or missing, for whom, observed where. No solution words in this section.

## 2. Evidence the problem exists
Bullets. Each one is a link, a log line, a metric with a date, a support message, a failing test, or "assumed, not observed". If every bullet is "assumed", this ADR is a hypothesis and the decision below must be the cheapest test of it, not the full build.

## 3. Success metric, with a date
One measurable statement: "<metric> moves from <baseline> to <target> by <date>". Name where the metric is read (telemetry event, query, dashboard). If it cannot be measured with what exists, the first step of the decision is to make it measurable.

## 4. Alternatives considered
A table. The first row is always "Do nothing".
| Alternative | Meets the success metric? | Cost | Why rejected or chosen |
| --- | --- | --- | --- |
| Do nothing | | | |
| ... | | | |

## 5. Decision
What will be built or changed, in enough detail that an implementing agent cannot reasonably add scope. List what is explicitly out of scope.

## 6. Kill criteria
"If <observation> by <date>, this decision is reversed." At least one line. The observation must be something a person or a script can check without judgement (a number, an event count, a failing check, a cost figure). Put the date in the calendar.

## 7. Reversibility
How the decision is undone if a kill criterion fires: which commits, migrations, flags, data or contracts are involved, and the estimated effort. If the honest answer is "it cannot be undone", the Tier is `irreversible` and the founder must read this ADR before any implementation starts.

## 8. Consequences
What becomes easier, what becomes harder, what new guardrail (ArchUnit rule, Modulith boundary, CI check) encodes this decision so that parallel agents honour it. A decision that cannot be expressed as a check needs a sentence saying why.

## 9. Who challenged it
- Critic report: link to the plan-critic comment, with its verdict copied here.
- Second critic (if Tier is irreversible, money, security or public): model and vendor, verdict.
- Founder's one-line expectation written before reading the critic report, and whether the report changed it.
- Pre-mortem (optional, plan level only): "It is <date plus six months> and this failed because ..."
