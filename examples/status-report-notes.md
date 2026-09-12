# Q3 Platform Migration — rehearsal notes

Slot: 8 min · Slides: 4 · Language: en

## Slide 1 — Q3 platform migration is on plan

**Say (~90s):**

Thanks for the time. Status in one line: the Q3 migration is still on plan. Seventy-two percent of services now run on the new runtime. We have had zero P1 incidents in the last thirty days. Two teams still need a cutover window in October, and that is the main thing I need from this room.

**Watch for:**

- "On plan" versus "ahead" — we are on plan, not ahead
- Questions about the remaining 28% — point to slide 2

## Slide 2 — Core domains ahead; data plane behind

**Say (~2m):**

Where we actually are. API gateway and auth are complete. The worker fleet is at eighty-four percent. The data plane is the lagging domain at fifty-one percent. That gap is not a staffing problem; it is dual-write soak. We are not going to cut over search until the error rate stays under one-tenth of a percent for a full week.

**Watch for:**

- Pressure to skip soak — refuse politely, reference the exit criterion
- Ask for the soak dashboard link after the meeting

## Slide 3 — Two asks this week

**Say (~2m):**

Two decisions. First, approve the October twelfth cutover window for billing workers. Second, fund one extra week of dual-write soak for search. If we do not get the second ask, the October gate slips for the data plane only — not for billing.

**Watch for:**

- Budget owner present: land the funding ask here
- If no decision today: name a decision date before leaving

## Slide 4 — Exit criterion for the October gate

**Say (~90s):**

Close on the exit bar. All P0 services green on the new runtime for seven consecutive days. One rollback drill per remaining domain. Search dual-write error rate under zero point one percent. If those three hold, we call the gate. I will send the offline HTML pack and the soak dashboard after this.

**Watch for:**

- Do not reopen slide 2 debates here
- Offer offline pack immediately
