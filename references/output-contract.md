# Output contract

Optional structured form of a deck. Use it when the user asks for JSON/YAML, a machine-readable outline, or a payload for a rendering script. Default human output stays Markdown (see SKILL.md Step 5).

## Schema

Top-level object:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `schema_version` | string | yes | Always `"1.0"` for this contract |
| `meta` | object | yes | Deck-level metadata |
| `slides` | array | yes | One entry per slide, in presentation order |

### `meta`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | string | yes | Deck title |
| `audience` | string | yes | Who is in the room |
| `purpose` | string | yes | One of: `inform`, `persuade`, `pitch`, `report`, `train` |
| `language` | string | yes | BCP-47 tag, e.g. `en`, `zh-CN` |
| `target_minutes` | number | yes | Requested talk length |
| `slide_count` | integer | yes | Must equal `len(slides)` |
| `est_minutes` | number | yes | Sum of slide timings, rounded to 1 decimal |
| `structure_id` | string | no | Structure key from slide-structures, e.g. `status-report` |

### `slides[]`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | integer | yes | 1-based slide number |
| `title` | string | yes | Claim-style headline (full sentence, not a label) |
| `bullets` | string[] | yes | 3–5 items, each under ~12 words |
| `visual` | string | yes | One concrete visual suggestion |
| `speaker_notes` | string | yes | 2–3 sentences the presenter can say out loud |
| `est_seconds` | integer | yes | Estimated talk time for this slide |

Do not invent extra top-level keys. If the user needs custom fields, put them under `meta.extra` as a free-form object.

## Timing model

Estimate from `speaker_notes` plus a short on-screen beat:

| Language | Speaking rate | Slide overhead |
|----------|---------------|----------------|
| English (`en`) | 130 words / minute | +8 seconds |
| Chinese (`zh-CN`) | 240 characters / minute | +8 seconds |

```
est_seconds ≈ ceil( words_or_chars / rate_per_second ) + 8
est_minutes = round( sum(est_seconds) / 60 , 1 )
```

Rules:

- Count English words as whitespace-separated tokens; count Chinese characters (ignore punctuation).
- Title is spoken once at the start of the slide; include it in the word/char count.
- After summing, compare `est_minutes` to `meta.target_minutes`. If they differ by more than 15%, either trim notes, drop a slide, or set `meta.target_minutes` to the real estimate and say so in the Markdown companion.
- A closing Q&A slide can use a fixed 30–60 seconds; do not inflate notes just to fill time.

## JSON example shape

```json
{
  "schema_version": "1.0",
  "meta": {
    "title": "B2B Expense-Tracking SaaS — Pitch",
    "audience": "startup CFOs",
    "purpose": "pitch",
    "language": "en",
    "target_minutes": 10,
    "slide_count": 3,
    "est_minutes": 3.2,
    "structure_id": "business-pitch"
  },
  "slides": [
    {
      "id": 1,
      "title": "Finance teams lose 6 hours a week to manual expense reports",
      "bullets": [
        "68% of expense reports are still processed by hand",
        "Average cost to process one report: $26",
        "The problem scales with every new hire"
      ],
      "visual": "bar chart of hours lost vs company size",
      "speaker_notes": "Start with the number that hurts: six hours a week per finance team member.",
      "est_seconds": 28
    }
  ]
}
```

A full worked deck lives at `examples/status-report.json`.

## YAML

Same fields and nesting as JSON. Use YAML when the user prefers a diff-friendly edit format; keep the same key names.

```yaml
schema_version: "1.0"
meta:
  title: B2B Expense-Tracking SaaS — Pitch
  audience: startup CFOs
  purpose: pitch
  language: en
  target_minutes: 10
  slide_count: 1
  est_minutes: 0.5
slides:
  - id: 1
    title: Finance teams lose 6 hours a week to manual expense reports
    bullets:
      - 68% of expense reports are still processed by hand
      - Average cost to process one report: $26
    visual: bar chart of hours lost vs company size
    speaker_notes: Start with the number that hurts: six hours a week.
    est_seconds: 28
```

## Validation checklist

Before delivering structured output, check:

1. `schema_version` is `"1.0"`.
2. `meta.slide_count` equals the number of entries in `slides`.
3. Slide `id` values are `1..N` with no gaps.
4. Every slide has non-empty `title`, `bullets`, `visual`, `speaker_notes`, `est_seconds`.
5. `bullets.length` is between 1 and 5 (prefer 3–5).
6. `est_minutes` matches `sum(est_seconds)/60` within 0.1.
7. Language of titles/bullets/notes matches `meta.language`.
8. Output is valid JSON (or valid YAML) — parse it mentally; no trailing commas, no comments in JSON.

## What this is not

- Not a `.pptx` file format. This is an outline payload; rendering is a later step (see ROADMAP v1.3).
- Not required. Keep the default Markdown deck unless the user asks for structure.
