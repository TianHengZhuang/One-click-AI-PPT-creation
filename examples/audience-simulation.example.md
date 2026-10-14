# Worked example — Audience simulation

Request: "The Q3 migration status deck goes to the VP of Engineering and peer leads on Thursday. Stress-test the room before I present it."

Deck simulated: `examples/status-report.md` (8 slides, ~5-minute slot, purpose: status report that asks for two decisions).

Seats chosen:

| Seat | Perspective | Why this seat |
|------|-------------|---------------|
| `decision-maker` | VP Engineering — owns the quarter, signs the budget | Slide 6 asks her for two decisions |
| `skeptic` | Peer lead — owns one of the six remaining services | Carries the migration work she did not ask for |
| `affected` | On-call lead — runs the cut-over weekend | Slide 4 says on-call load is up 30% |

---

## Seat: decision-maker

| # | Question | Anchor | Status |
|---|----------|--------|--------|
| 1 | "You want me to accept 15 October as the plan of record. What happens to the quarter if billing slips by two weeks?" | Slide 5, "No buffer if that slips" | answered in substance, not in consequence |
| 2 | "Pre-approve the dual-write fallback. What is the number?" | Slide 6, decision card 2 | gap — no cost anywhere in the deck |
| 3 | "41% of the error budget is gone and six services are still ahead of you. Do I need to worry about availability in November?" | Slide 3 + slide 1 | gap — the two numbers never meet on a slide |

## Seat: skeptic (peer lead)

| # | Question | Anchor | Status |
|---|----------|--------|--------|
| 1 | "Which six services are left, and is mine one of them?" | Slide 1 says 6 of 20, slide 7 says 15-17 | partial — the deck never names the set |
| 2 | "Rollback was exercised twice. Was either of them on the services that carry 80% of traffic?" | Slide 2 | gap — the audience will assume the answer is no |
| 3 | "Load tests run in parallel with cut-overs. In parallel with my team's release too?" | Slide 7 | partial — no owner or calendar attached |

## Seat: affected (on-call lead)

| # | Question | Anchor | Status |
|---|----------|--------|--------|
| 1 | "On-call load is up 30%. For how many more weekends, and who absorbs it after the cut-over?" | Slide 4 | gap — issue is listed, owner and end date are not |
| 2 | "If the cut-over goes wrong at 02:00, is the runbook the same 90-minute path we rehearsed?" | Slide 2 | answered — runbook and rollback rehearsal cover it |
| 3 | "Two rollbacks in production, both clean. What did the first one cost in engineer hours?" | Slide 2 | gap — "clean" hides the cost |

---

## Verdict

The deck survives the room. The story is one line — 70% done, no customer impact, the risk sits in the last third — and every seat can repeat it.

Three gaps are worth closing before Thursday, in this order:

1. **The cost of the fallback.** Slide 6 asks for pre-approval with no number. Put the figure on the card, or carry it in the notes so the answer is ready.
2. **Error budget against the remaining work.** 41% consumed plus six services carrying 80% of traffic is a question the VP will ask. Pair the two facts, or say plainly that the budget holds.
3. **The on-call burden.** Say how many weekends and who owns it after the window closes. This is the seat that can kill the plan in the room.

Two smaller items for the notes: name the six remaining services, and say whether either rollback rehearsal touched one of them.

## Recommended deck changes

| Change | Slide | Why |
|--------|-------|-----|
| Add the fallback cost to the decision card | 6 | Turns a vague pre-approval into a signature |
| Add one line pairing the error budget with the remaining six services | 3 | Pre-empts the maths the VP will do out loud |
| Add weekends remaining and the post-window owner | 4 | Answers the on-call seat without being asked |
| Name the six services in the notes | 1 | The skeptic's first question, answered before the open floor |

Keep the structure. Change nothing else — the recap and the closing question slide are what let the room decide in five minutes.
