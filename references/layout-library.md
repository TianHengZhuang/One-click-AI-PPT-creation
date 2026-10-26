# Layout library

`assets/layouts.json` holds the fourteen slide roles as coordinates, not pictures: a
16:9 canvas, four bands per variant, and the copy budget each variant can carry.
The library is data — a script or a human can read it, and nothing in it needs
python-pptx.

Use it for three things:

1. **Picking a layout deliberately.** Every variant has a `when` line: the situation
   it was drawn for. Pick by `when`, not by looks.
2. **Sizing the copy.** `limits.bullets`, `limits.words_per_bullet` and
   `limits.headline_words` are what fits the band without resizing type.
   `tools/deck_qa.py` reads them, so a payload that overflows a role gets flagged.
3. **Handing off to a designer or a renderer.** `bands` gives x/y/w/h in inches for
   headline, copy, data and footnote, so a template or a script can place shapes
   without guessing.

## Canvas

| Field | Value |
|-------|-------|
| `canvas.width` | 13.333 in (16:9) |
| `canvas.height` | 7.5 in |
| margin | 0.62 in left and right, applied inside every band |

## Roles

Fourteen roles, 31 variants. Each role carries a `purpose` line: the one job the role
does. If a slide needs two of these jobs, it is two slides.

| Role | Variants | Bullets | Words per bullet | Headline words |
|------|----------|---------|------------------|----------------|
| `title` | title-left, title-centred, title-band | 0–3 | — | 9–12 |
| `agenda` | agenda-single, agenda-two-column | 3–6 | 8–10 | 8 |
| `section-break` | section-left, section-full-bleed | 0–2 | — | 6–8 |
| `bullet-list` | list-full, list-margin, list-indented | 2–5 | 10–14 | 14 |
| `two-column` | two-even, two-wide-left | 2–6 | 9–11 | 14 |
| `chart` | chart-right, chart-full, chart-left | 0–3 | 10 | 12 |
| `table` | table-full, table-with-lead | 0–2 | 10 | 12 |
| `quote` | quote-centred, quote-attribution | 0–2 | — | 10–12 |
| `comparison` | compare-two, compare-three | 2–6 | 6–8 | 14 |
| `timeline` | timeline-horizontal, timeline-vertical | 3–6 | 6–10 | 12 |
| `stat-row` | stats-three, stats-four | 3–4 | 4–5 | 12 |
| `image-left` | image-left-half, image-left-thumb | 2–5 | 10–11 | 14 |
| `image-full` | image-full-bleed, image-full-caption | 0–2 | — | 8–10 |
| `closing` | closing-centred, closing-contact | 1–4 | — | 8–10 |

Ranges are the min and max across a role's variants; a dash means the role has no body
copy to measure. `tools/deck_qa.py` compares against the widest variant, so a slide is
only flagged when it would overflow every layout of its role.

`data` in a variant's `limits` names what belongs in the data band: `chart`,
`table`, `stats`, `image` or `none`. A `chart` slide with no chart is a bullet
slide wearing the wrong role.

## Bands

```json
"bands": {
  "headline": {"x": 0.62, "y": 0.55, "w": 12.093, "h": 1.05},
  "copy":     {"x": 0.62, "y": 1.62, "w": 5.079,  "h": 4.68},
  "data":     {"x": 6.119, "y": 1.62, "w": 6.594, "h": 4.68},
  "footnote": {"x": 0.62, "y": 6.42, "w": 12.093, "h": 0.38}
}
```

- The headline band never moves: y 0.55, height 1.05. Slide numbers go in the footnote band.
- `copy` and `data` split the middle band; `chart-full` and `image-full` give the whole
  width to `data` and shrink `copy` to a single strip.
- A band that would be smaller than 0.4 in in height is not a band; it is a mistake.

## Adding a variant

1. Copy an existing variant of the same role, give it a new `id` and a `when` line.
2. Keep the headline band fixed; move only `copy` / `data`.
3. Set `limits` from the width: about 12 characters per inch at 15pt.
4. Run `python tools/deck_qa.py examples/data-layer.example.json --strict` — the limits
   are read from this file, so a broken entry shows up as a role that fails its own slides.

## Relationship to the renderer

`tools/render_pptx.py` places slides through a slide master (`references/master-mapping.md`),
not through this file: a corporate template owns its own geometry. The library is the
reference geometry for decks built without a template, and the source of truth for copy
budgets in every deck. When the two disagree about how much copy fits, the library wins —
it is the one that gets linted.
