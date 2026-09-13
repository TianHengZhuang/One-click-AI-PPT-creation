# Worked example — Status report

Request: "Create a status report deck for the Q3 platform migration. Audience: VP Engineering and peer leads. 8 slides, about 5 minutes."

Structure used: 2. Status report.

---

## Slide 1 — Migration is 70% complete and on the original schedule

- 14 of 20 services cut over
- Zero customer-visible incidents this quarter
- The remaining 6 services carry 80% of traffic

Visual: progress bar with all 20 services marked, the last 6 in a contrasting colour

Notes: "We are at 70% with no customer impact. The remaining six services carry most of our traffic, so the last third is where the risk lives."

## Slide 2 — Wins since the last report

- Cut-over runbook reduced average migration time from 6 hours to 90 minutes
- Two teams that were blocked on tooling are now self-serving
- Rollback was exercised twice in production, both clean

Visual: before/after timeline of a single cut-over

Notes: "The runbook change is the reason we caught up. Rollback has been tested for real, not on paper."

## Slide 3 — Metrics dashboard

- Availability 99.97% against a 99.95% target
- p95 latency down 12% after the second cut-over
- Error budget consumed: 41% of the quarter

Visual: three-metric dashboard row

Notes: "Latency improved as a side effect of the new routing layer. Error budget is comfortable."

## Slide 4 — Two issues are open

- Service 15 has a schema dependency we cannot cut over until the billing team ships
- On-call load is up 30% during cut-over weekends

Visual: table of the two issues with owner and age

Notes: "Neither issue threatens the schedule yet. The billing dependency is the one to watch."

## Slide 5 — The billing dependency is the schedule risk

- Billing ships on 15 October, three weeks before our cut-over window
- No buffer if that slips
- Alternative path exists but costs two extra weeks of dual-write

Visual: dependency timeline with the two paths

Notes: "If billing slips past 15 October, we choose between missing the quarter or paying for the dual-write path."

## Slide 6 — Two decisions are needed today

- Accept the 15 October dependency as the plan of record
- Pre-approve the dual-write fallback budget

Visual: two decision cards with the owner of each

Notes: "These are the only two things I need from this room."

## Slide 7 — Next steps

- Services 15-17 scheduled for weeks 1-3 of October
- Load tests for the remaining six run in parallel
- Weekly risk review with the billing lead starts Friday

Visual: three-lane schedule through the end of the quarter

Notes: "The last three services are the ones that need the most rehearsal."

## Slide 8 — Questions

- Risks I have not listed
- Constraints from your teams

Visual: none

Notes: "Open floor. I would rather hear the objection now than in November."
