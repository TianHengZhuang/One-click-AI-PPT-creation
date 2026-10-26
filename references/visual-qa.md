# Visual QA

`tools/deck_lint.py` asks whether the copies of a deck agree with each other.
`tools/deck_qa.py` asks a different question: **will these slides work in a room?**
It reads the payload, the copy budgets in `assets/layouts.json`, and — when you name one —
a theme from `assets/themes/`.

```bash
python tools/deck_qa.py deck.json
python tools/deck_qa.py deck.json --theme swiss
python tools/deck_qa.py deck.json --strict --report qa.md
python tools/deck_qa.py deck.json --json
```

Standard library only. Exit 0 when clean, 1 on any error (or on any warning with
`--strict`). Worked sample: `examples/qa-report.example.md`.

## What it measures

| Rule | Code | Severity | Fires when |
|------|------|----------|------------|
| Headline too long | QA101 | warn | the headline exceeds the role's headline budget |
| Headline is a label | QA102 | warn | a one- or two-word headline on a body slide ("Metrics", "Next steps") |
| Bullet count | QA103 | error / warn | zero bullets on a body slide, more than five, or outside the role's band |
| Bullet too long | QA104 | warn | a bullet exceeds the role's words-per-bullet |
| Figures without data | QA105 | info | two-digit figures on a slide with no chart or table |
| Copy beside data | QA106 | warn | more than three bullets next to a chart or table |
| No speaker notes | QA107 | error | empty notes |
| Notes out of pace | QA108 | warn | the notes read above 3.2 words per second for `est_seconds` |
| No visual suggestion | QA109 | error | `visual` is empty |
| Slide word budget | QA110 | warn | headline plus bullets exceed 45 words |
| Chart overload | QA111 | warn | more than 3 series, more than 8 categories, or a pie with more than 6 slices |
| Table density | QA112 | warn | more than 6 rows, or a cell that reads as a sentence |
| Repeated openers | QA113 | warn | three headlines in a row open with the same word |
| Unreadable theme | QA114 | error | the theme breaks a contrast floor (see `references/themes.md`) |

Severities are deliberate. **Error** means the slide cannot do its job: no notes, no visual,
no body copy, too much copy to read. **Warn** means it works but the room will feel it.
**Info** means an opportunity — a figure that would land harder as a chart — and never
costs a point.

Dating and counting are not figures: `15 October`, `October 15`, `2025` and single digits
are ignored by QA105. `99.97%`, `90 minutes`, `-17` and `30%` are figures.

## Scoring

Start at 100; −15 per error, −5 per warning, 0 per info; floor at 0.

| Score | Grade | Reading |
|-------|-------|---------|
| 90–100 | A | Ship it |
| 75–89 | B | Fix the flagged lines, then ship |
| 60–74 | C | The structure is fighting the room; rework the slides, not the words |
| below 60 | D | Rewrite the deck |

The score is a review aid, not a certificate: `--strict` in CI, plain in conversation. A
deck that trips no rule scores 100.
`examples/status-report.json` scores 80 and the gaps it reports are real: a label headline,
one 15-word bullet, three slides carrying figures with no chart.

## Reading a report

Findings are grouped per slide and carry a slide number, the code, the severity and one
sentence about the fix. Fix in this order:

1. **Errors** — the deck is not presentable yet.
2. **Warn on copy** (QA101, QA102, QA104, QA110) — cut words; do not shrink type.
3. **Warn on data** (QA106, QA111, QA112) — the slide is doing two jobs or the table is a document.
4. **Info** (QA105) — a chart would say it faster, but the slide still works as prose.

Two patterns worth knowing by name:

- **A data slide drawn as prose.** Four bullets each carrying a figure and no chart: the
  audience cannot compare numbers they have to hold in their head. Fix by shipping a
  structured `chart` block; see `references/output-contract.md`.
- **A label headline.** "Metrics" tells the room where it is, not what to think. Fix by
  turning it into the claim the numbers support.

## When to run it

- After drafting the payload, before rendering: catches density problems while copy is
  still cheap to change.
- After theming, with `--theme`: catches a palette that cannot be read.
- In CI, with `--strict` and `--json`.
- Never as a gate on a deck the user asked to be dense — a data appendix is allowed to
  break QA110; say so in the hand-off instead of trimming it.

## Relationship to the other checks

| Tool | Question |
|------|----------|
| `tools/source_extract.py` | what does the source actually say |
| `tools/deck_lint.py` | do the copies of the deck agree |
| `tools/deck_review.py` | is the story worth presenting |
| `tools/deck_qa.py` | will the slides work in the room |
| `tools/render_pptx.py` | does it become a real file |
| `tools/theme_apply.py` | does it look like the brand |

QA runs last before the file leaves, because it is the cheapest check that still catches
what a reader would notice first.
