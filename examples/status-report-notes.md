# Q3 Platform Migration — Status Report — rehearsal notes

Slot: 5 min · Slides: 8 · Language: en

## Slide 1 — Migration is 70% complete and on the original schedule

**Say (~36s):**

Thanks for the time. Status in one line: we are seventy percent through the migration and still on the original schedule. Fourteen of the twenty services are cut over, with zero customer-visible incidents this quarter. The remaining six carry about eighty percent of our traffic, so the last third is where the risk lives. Does anyone in the room read that remaining six differently?

**Watch for:**

- Anyone reading "70%" as slippage — it is the planned checkpoint, not a miss
- Questions about the services already behind us — point to slide 2

## Slide 2 — Wins since the last report

**Say (~40s):**

Two things went right since the last report. The cut-over runbook took average migration time from six hours down to ninety minutes, and that is the reason we caught up. Two teams that were blocked on tooling now self-serve, and rollback ran twice in production, both clean. Which of those two changes do you think travels best to your teams?

**Watch for:**

- Is the runbook change permanent? Yes, it is the new standard
- Pressure to skip the rollback drill — refuse it, that drill is our proof

## Slide 3 — Metrics dashboard

**Say (~38s):**

Availability is ninety-nine point nine seven percent against a ninety-nine point nine five target. Latency p95 is down twelve percent after the second cut-over, which is a side effect of the new routing layer. Error budget consumed is forty-one percent of the quarter, so we are comfortable. Of these three numbers, which one would you watch hardest through October?

**Watch for:**

- Whether latency holds under peak load, the load tests cover that
- Requests to spend the error budget — hold it for the cut-over weekends

## Slide 4 — Two issues are open

**Say (~36s):**

Two issues are open, and neither threatens the schedule yet. Service fifteen has a schema dependency that cannot cut over until billing ships. On-call load is up thirty percent during cut-over weekends, and that is a staffing question rather than a technical one. Has anyone seen a heavier on-call weekend than that?

**Watch for:**

- On-call burnout raised here — name the rotation fix before it becomes a debate
- The billing dependency is the one to watch — hand over to slide 5

## Slide 5 — The billing dependency is the schedule risk

**Say (~40s):**

This is the risk slide. Billing ships on the fifteenth of October, three weeks before our cut-over window, and there is no buffer if that slips. An alternative path exists, but it costs two extra weeks of dual-write, and that is the trade on the table. If that date slips, which path would you take?

**Watch for:**

- Anyone proposing we absorb a slip silently, surface both options instead
- Ask for the dependency owner by name, and for a weekly signal

## Slide 6 — Two decisions are needed today

**Say (~28s):**

I need two decisions from this room today. First, accept the fifteenth of October dependency as the plan of record. Second, pre-approve the dual-write fallback budget so we can move the week it slips. Can I take those two as agreed today?

**Watch for:**

- Budget owner present: land the second ask here
- If no decision today: name a decision date before leaving

## Slide 7 — Next steps

**Say (~38s):**

Next steps. Services fifteen through seventeen are scheduled for weeks one to three of October, and load tests for the remaining six run in parallel. Weekly risk review with the billing lead starts Friday, and the last three services need the most rehearsal. Who owns the load tests, and by when?

**Watch for:**

- Capacity objections, the parallel lane is already budgeted
- Who owns the load tests, and by when

## Slide 8 — Questions

**Say (~30s):**

Open floor. I would rather hear the objection now than in November. Risks I have not listed, and constraints from your teams, are what I am listening for.

**Watch for:**

- Keep answers to one minute; take deep dives offline
- Offer the offline HTML pack and the metrics dashboard after the meeting
