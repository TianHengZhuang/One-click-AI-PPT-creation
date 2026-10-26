# Output contract

Optional structured form of a deck. Use it when the user asks for JSON/YAML, a machine-readable outline, or a payload for a rendering script. Default human output stays Markdown (see SKILL.md Step 5).

## Schema

Top-level object:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `schema_version` | string | yes | `"1.1"` (or `"1.0"` for text-only decks); 1.1 adds the optional data layer |
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
| `chart` | object | no | Native chart, schema 1.1 — see [Data layer](#data-layer-schema-11) |
| `table` | object | no | Native table, schema 1.1 — see [Data layer](#data-layer-schema-11) |

Do not invent extra top-level keys. If the user needs custom fields, put them under `meta.extra` as a free-form object.

## Data layer (schema 1.1)

A slide may carry **one** structured data block instead of leaving the figure to the
`visual` sentence. The renderer turns it into a native, editable chart or table; the
Markdown deck keeps the `visual` line, so nothing is lost for text-only consumers.

Rules:

- One data block per slide: never `chart` and `table` together.
- Not on slide 1 (the title slide) and not on the closing slide.
- `bullets` stay **3 or fewer** next to a data block; the deck copy shrinks to a side column.
- Keep `visual` filled anyway — it is the fallback for Markdown and for slides that
  lose their data block on a customer template.
- Aggregates and comparisons only. If the audience needs the cell-level detail, ship
  the table; if they need the shape of the trend, ship the chart.

### `chart`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `type` | string | no | `column` (default), `bar`, `line`, `area`, `pie`, `doughnut`, `stacked-column`, `stacked-bar` |
| `categories` | string[] | yes | 2–12 labels, in reading order |
| `series` | object[] | yes | 1–4 series |
| `series[].name` | string | no | Legend label; defaults to `Series` |
| `series[].values` | number[] | yes | One value per category, same length as `categories` |
| `title` | string | no | Chart title; omit if the slide headline already says it |
| `unit` | string | no | Axis label, e.g. `hours`, `%`, `ms` |
| `source` | string | no | Rendered as a small `Source:` line at the bottom |
| `emphasis` | integer[] | no | Category indexes to draw in the accent colour |

`pie` and `doughnut` plot the first series only. Line and column charts want a real
axis scale — do not truncate the value axis to exaggerate a difference.

### `table`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `columns` | string[] | yes | 2–6 headers |
| `rows` | array[] | yes | 1–8 rows, each with exactly `len(columns)` scalar cells |
| `caption` | string | no | Shown in the speaker notes |
| `source` | string | no | Rendered as a small `Source:` line at the bottom |

Cells are short labels or formatted values (`"$1.2M"`, `"+3%"`), not sentences.
Eight rows is the ceiling: a table the audience cannot read in one glance belongs in
the appendix.

### Example

```json
{
  "id": 2,
  "title": "Cut-over time fell by three quarters",
  "bullets": ["Median cut-over: 6 hours to 90 minutes"],
  "chart": {
    "type": "bar",
    "title": "Median cut-over time, hours",
    "categories": ["Q4 baseline", "Q1", "Q2", "Q3"],
    "series": [{ "name": "Median hours", "values": [7.5, 6.0, 3.2, 1.5] }],
    "unit": "hours",
    "emphasis": [3],
    "source": "Platform team runbook log, 41 cut-overs"
  },
  "visual": "bar chart of median cut-over hours by quarter",
  "speaker_notes": "The runbook change is why we caught up.",
  "est_seconds": 40
}
```

See `examples/data-layer.example.json` for a full six-slide payload.

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

1. `schema_version` is `"1.1"` when a data layer is present, `"1.0"` otherwise.
2. `meta.slide_count` equals the number of entries in `slides`.
3. Slide `id` values are `1..N` with no gaps.
4. Every slide has non-empty `title`, `bullets`, `visual`, `speaker_notes`, `est_seconds`.
5. `bullets.length` is between 1 and 5 (prefer 3–5).
6. `est_minutes` matches `sum(est_seconds)/60` within 0.1.
7. Language of titles/bullets/notes matches `meta.language`.
8. Output is valid JSON (or valid YAML) — parse it mentally; no trailing commas, no comments in JSON.
9. At most one of `chart` / `table` per slide, never on the first or last slide.
10. Every `series[].values` is the same length as `categories`; every table row is as
    long as `columns`.
11. `python tools/render_pptx.py <payload> --check` passes when the user asked for a file.

## What this is not

- Not a `.pptx` file format. This is an outline payload; rendering is a later step (see ROADMAP v1.3).
- Not required. Keep the default Markdown deck unless the user asks for structure.
