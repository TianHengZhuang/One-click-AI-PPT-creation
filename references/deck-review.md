# Deck review

Audit a deck that already exists. `deck_review` reads a finished Markdown deck or an output-contract JSON payload and reports what a hand-off would be blocked on, what is worth a second look, and how good the deck is on structure, copy, evidence and delivery.

Use it in two situations:

1. **Before hand-off.** Run it on the deck you just wrote, fix what it reports, then run the export checklist.
2. **On someone else's deck.** Run it on a deck you were asked to review. The report is the review - no rewriting, no re-planning.

## Running it

```bash
python tools/deck_review.py examples/status-report.md
python tools/deck_review.py examples/status-report.json --json
python tools/deck_review.py deck.md --slot 5 --min-score 85 --out review.md
```

| Flag | Effect |
|------|--------|
| `--slot MINUTES` | The slot the deck has to fill. Turns on the slot-drift warning. |
| `--min-score N` | Fail (exit 1) when the score lands below N. |
| `--strict` | Warnings fail the run too, not just hard gates. |
| `--json` | Emit the review as machine-readable JSON instead of text. |
| `--out PATH` | Write the Markdown report to a file. |
| `--quiet` | Summary and scores only, no finding list. |

`--json` and `--out` stack: the JSON report goes to stdout and the Markdown report to the file. Exit status is `1` when a hard gate fails, when the score is under `--min-score`, or (`--strict`) when there is any warning. Standard library only.

## Inputs

- **A Markdown deck.** Slides are `## Slide N - Headline`, with bullets, and optional `Visual:` and `Notes:` lines. This is the format the skill writes, so the common case is a file you already have.
- **An output-contract JSON payload.** Same schema `tools/deck_lint.py` validates (`schema_version`, `meta`, `slides`). Coverage numbers come from `meta.target_minutes` and `meta.est_minutes`.
- **Either, in Chinese or English.** The language is detected from the deck text; the timing model switches to 240 characters per minute and the text rules switch to characters instead of words.

## Hard gates

These do not warn. They block.

| Code | Meaning | Fix |
|------|---------|-----|
| `no-slides` | Nothing parsed - wrong file, or headings that do not match the slide format | Point the tool at the deck, or fix the headings |
| `headline-missing` | A slide with no headline | Give it a claim (design-guide: one message per slide) |
| `headline-duplicate` | Two slides carry the same headline | Merge them or retitle one |
| `bullets-empty` | A slide with no bullets, except the closing slide | Add the evidence, or make it the closing slide |
| `notes-missing` | A slide with no speaker notes | Write the two or three sentences the presenter says |

## Warnings

| Code | Dimension | Trigger |
|------|-----------|---------|
| `headline-label` | structure | Headline is a label ("Overview", "Next steps") instead of a claim |
| `bullets-too-many` | structure | More than 5 bullets on a slide |
| `bullet-nested` | copy | Nested bullets |
| `no-closing` | structure | Last slide is not an ask, a decision or a question slide |
| `bullet-long` | copy | Bullet over 12 words (en) or 24 characters (zh) |
| `bullet-paragraph` | copy | Over 20 words (en) or 40 characters (zh) - that is a sentence, move it to the notes |
| `bullet-two-ideas` | copy | Bullet joins two ideas with "and" (en), or "并且 / 而且 / 以及 / 同时 / ；" (zh) |
| `passive-voice` | copy | "was/were/been + -ed" in a bullet (en), or 被字句 (zh) |
| `cliche` | copy | Stock phrase from the jargon list ("leverage", "best-in-class", ...); in zh, four-character stacking ("降本增效、提质创优") |
| `notes-short` | delivery | Notes too short to speak (under about 4 seconds) |
| `notes-long` | delivery | Notes over about 40 seconds for one slide |
| `visual-missing` | evidence | No `Visual:` line on the slide |
| `visual-generic` | evidence | Visual names the medium ("image", "chart") instead of the evidence |
| `slot-drift` | delivery | Deck time is more than 15% off the slot (`output-contract.md`) |
| `no-metric` | copy | Fewer than half the body slides carry a number |
| `metric-source` | evidence | Metric claims with no source or "internal" label anywhere in the deck |

## Scoring

Four dimensions, weighted:

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| structure | 30% | One message per slide, the deck has a shape, the last slide closes |
| copy | 30% | Claims, active voice, short bullets, no jargon |
| evidence | 20% | Numbers with sources, a visual per slide that shows the evidence |
| delivery | 20% | Notes within the time budget, deck fits the slot |

Each dimension starts at 100. Every hard gate in that dimension costs 25 points, every warning costs 6. The weighted total is the score.

| Verdict | Score | What it means |
|---------|-------|---------------|
| **READY** | ≥ 85, no hard gate failed | Hand it over; fix warnings if there is time |
| **REVISE** | ≥ 70, or warnings worth the trip | Fix the listed items, then re-run |
| **REWRITE** | < 70, or any hard gate failed | The deck is not ready - rebuild the failing slides |

## Chinese decks

The 130 words-per-minute English model and the 240 characters-per-minute Chinese model are both in `references/output-contract.md`, so the review follows the deck's language:

- Bullet length and paragraph length switch to characters.
- Passive voice looks for 被字句, two-idea bullets look for the Chinese joiners and the full-width semicolon, and cliches look for four-character stacking (references/zh-cn-adaptation.md).
- Notes length is derived from the same speaking budget: about 16 characters minimum and 160 maximum per slide, against 48 and 477 in English.
- Headline labels are matched against the Chinese label list (概览, 下一步, 问题, ...).

## Relationship to deck_lint

`deck_lint.py` checks the pack: the Markdown, the JSON, the notes and the HTML agree with each other and with the output contract. It is a correctness check on copies of the same deck.

`deck_review.py` checks one deck on its own merits: message, copy, evidence, delivery. Different question, so run both before a hand-off:

```bash
python tools/deck_review.py deck.md --slot 5
python tools/deck_lint.py deck.md
```

## What a reviewer does with the report

1. Read the verdict. READY means nothing below is blocking.
2. Fix hard gates first, in slide order.
3. Then the structure and copy warnings - headlines and bullets are what the room hears.
4. Then evidence: a number without a source is a question you cannot answer.
5. Never rewrite the author's message to satisfy a rule. Fix the wording, keep the point.

Worked example: `examples/deck-review.example.md`.
