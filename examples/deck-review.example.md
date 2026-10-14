# Worked example — Deck review

Request: "Review my Q3 migration status deck before I send it to the VP. Five-minute slot."

Deck reviewed: `examples/status-report.md` (the same deck as the Markdown, JSON, HTML and notes pack).

Command:

```bash
python tools/deck_review.py examples/status-report.md --slot 5 --out review.md
```

---

# Deck review - Worked example — Status report

- Source: `markdown` deck, 8 slides
- Estimated talk time: 2.4 min (notes alone carry 2.4 min)
- Slot: 5 min
- Verdict: **READY** - score 87/100
- Hard gates: pass

## Dimension scores

| Dimension | Score |
|-----------|-------|
| structure (30%) | 82 |
| copy (30%) | 82 |
| evidence (20%) | 94 |
| delivery (20%) | 94 |

## Warnings

| Slide | Finding | Fix |
|-------|---------|-----|
| 2 | passive voice: "Two teams that were blocked on tooling are now self-serving" | Rewrite the sentence in active voice. |
| 2 | passive voice: "Rollback was exercised twice in production, both clean" | Rewrite the sentence in active voice. |
| 3 | headline reads as a label, not a claim: "Metrics dashboard" | Rewrite the headline as a claim the audience could argue with. |
| 4 | 15-word bullet: "Service 15 has a schema dependency we cannot cut over unt..." | Cut the bullet to twelve words or fewer. |
| 7 | headline reads as a label, not a claim: "Next steps" | Rewrite the headline as a claim the audience could argue with. |
| 8 | headline reads as a label, not a claim: "Questions" | Rewrite the headline as a claim the audience could argue with. |
| deck | deck estimates 2.4 min against a 5 min slot (notes alone carry 2.4 min) | Cut slides or trim notes to fit the slot. |
| deck | metric claims carry no source or 'internal' label anywhere in the deck | Add a source or an 'internal' label before hand-off. |

## Holding up

- evidence: 94/100
- delivery: 94/100

## Next step

Hand over as is; fix the warnings only if there is time.

Fixes follow `references/copywriting-guide.md` and `references/design-guide.md`. Keep the author's content; change what the rules require.

---

## What the reviewer does with this

1. The deck is not blocked — no hard gate failed.
2. Fix the two headline labels first: "Metrics dashboard" and "Next steps" carry no message, so the audience reads instead of listening.
3. The slot warning is real but expected: the notes cover 2.4 minutes of a 5-minute slot. The presenter fills the rest, or the notes get a sentence each.
4. Add the source line before the deck leaves the building — the export checklist makes that a hard gate at hand-off, not at review.
5. Pass the same deck to `references/audience-simulation.md` if the room is hostile.
