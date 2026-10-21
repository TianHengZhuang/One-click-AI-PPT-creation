# Worked example — Crisis communication

Request: "Draft the 8-slide crisis communication deck for a platform outage that started this morning. Facts only, calm tone, for the customer-facing update."

Structure used: 18. Crisis communication.

---

## Slide 1 — A database migration left the platform intermittently down for 6 hours

- Outage began 07:40 UTC during a routine database migration
- ~40% of customers saw degraded or failed requests at the peak
- No customer data was lost; no unauthorized access detected

Visual: availability timeline with the outage window shaded

Notes: "State the facts in the first breath: what, when, how many. Do not guess at a cause you have not confirmed."

## Slide 2 — What we know and what we do not

- Confirmed: a migration rollback failed, blocking writes
- Confirmed: reads were restored first, at 10:15 UTC
- Not yet confirmed: the full trigger of the rollback failure

Visual: two-column list — "confirmed" vs "under investigation"

Notes: "The trust test is the gap between what we know and what we do not. Say both out loud and do not blur the line."

## Slide 3 — What we are doing right now

- Engineering reverted the migration and is validating the rollback
- Support is triaging every affected account with a status page
- A full post-incident review is scheduled, findings to be published

Visual: three action cards with owners

Notes: "People forgive an outage; they do not forgive being left in the dark. Show the work happening right now."

## Slide 4 — Who is affected and how we are reaching them

- Customers on the EU region are the primary group affected
- Email to all affected accounts went out at 08:15 UTC
- Live updates on the status page, refreshed every 30 minutes

Visual: map of affected regions with contact channels

Notes: "Name the affected group and the channel we used to reach them. Silence reads as indifference."

## Slide 5 — The message we are telling everyone

- "Your data is safe. Service is recovering. We will publish the full cause within 48 hours."
- One message, used verbatim across email, status page, and support
- No individual rep improvises a different answer

Visual: the single message, large, on one line

Notes: "One line, everyone says it exactly the same way. A consistent message is half the crisis response."

## Slide 6 — Timeline — what happens next

- Full service restore: target 16:00 UTC today
- Root-cause summary to all customers: within 24 hours
- Post-incident review published: within 5 business days

Visual: single timeline with the three commitments and owners

Notes: "Commit to dates, not adjectives. Every deadline here is one we can hit."

## Slide 7 — Risks and what we are watching

- Risk: a second region fails during re-sync — monitor on standby
- Risk: the rollback introduces data inconsistency — checksum runs underway
- Risk: support backlog grows — extra shifts assigned tonight

Visual: risk register with a mitigation next to each

Notes: "Show we are watching the things that could still go wrong. Paranoia here is reassuring."

## Slide 8 — Where to get the next update

- Status page: status.example.com, updated every 30 minutes
- Next customer email: 16:00 UTC with restore confirmation
- Questions: support@example.com, reply within 2 hours

Visual: the three channels with times

Notes: "End on the channel and the clock. The audience leaves knowing exactly where to look next."
