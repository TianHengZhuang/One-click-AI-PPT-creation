# Themes

Three themes ship in `assets/themes/`. Each is a JSON file of colours, fonts and sizes —
no images, no fonts to install, nothing that has to travel with a deck.

| Theme | Reads as | Use it for |
|-------|----------|------------|
| `consulting` | Navy ink, blue accent, generous side margin | Client work, board packs, anything reviewed by a partner |
| `swiss` | Black on white, one red accent, tight grid | Design reviews, product launches, a room that distrusts decoration |
| `editorial` | Warm paper, serif type, brick accent | Narrative decks, investor updates, anything read as well as watched |

## Applying one

```bash
python tools/theme_apply.py deck.pptx --theme swiss
python tools/theme_apply.py deck.pptx --theme editorial --out board_q3.pptx
python tools/theme_apply.py deck.pptx --theme swiss --check      # validate only
python tools/theme_apply.py --list
```

The tool restyles an existing `.pptx`: slide background, title and body type, chart
series colours, table header fills and cell type. It does not move shapes — geometry stays
with the renderer. Result: you can theme a deck that has already been through a designer's
hands, and re-theme it again without re-emitting the payload.

Needs `python-pptx` (the same optional dependency as the renderer). Without it the tool
exits 2 and prints the install line.

## What a theme file holds

```json
{
  "name": "swiss",
  "label": "Swiss",
  "when": "Design reviews, product launches, a room that distrusts decoration.",
  "palette": {
    "bg": "#FFFFFF", "ink": "#111111", "muted": "#555555",
    "accent": "#E4002B", "band": "#F2F2F2", "rule": "#D0D0D0",
    "on_accent": "#FFFFFF"
  },
  "font": {"title": "Helvetica Neue", "body": "Helvetica Neue", "table": "Helvetica Neue"},
  "size": {"title": 28, "section": 22, "body": 15, "footnote": 9, "table": 10},
  "chart_series": ["#E4002B", "#111111", "#8C8C8C", "#D9D9D9"],
  "table_header_fill": "#F2F2F2"
}
```

| Field | Meaning |
|-------|---------|
| `palette.bg` | slide background; every contrast check is measured against it |
| `palette.ink` | body and headline text |
| `palette.muted` | footnotes, sources, subdued labels |
| `palette.accent` | the one colour for calls to action and the key number |
| `palette.band` / `palette.rule` | table banding and hairline rules |
| `palette.on_accent` | text drawn on top of the accent colour |
| `font` | font names per role; a name the machine lacks falls back silently |
| `size` | points per role; sizes are floors, not suggestions |
| `chart_series` | bar/line colours in order; pies cycle through them per slice |
| `table_header_fill` | header row fill; body rows take `palette.bg` |

`chart_series` and `table_header_fill` are optional; without them charts take `accent` and
tables take `band`.

## Contrast floors

A theme is rejected by `--check` and by `tools/deck_qa.py --theme` when it cannot be read
from the back of a room:

| Pair | Floor | Why |
|------|-------|-----|
| `ink` on `bg` | 7:1 | body text at 15pt on a projector |
| `muted` on `bg` | 4.5:1 | footnotes still have to be legible |
| `accent` on `bg` | 3:1 | the accent is used for large numbers, never for sentences |
| `on_accent` on `accent` | 3:1 | text on a filled button or band |
| any `size` | ≥ 9pt | below this a projected slide is unreadable, whatever the brand book says |

Also rejected: a title that is not larger than the body, and a `size` or hex value that is
not a number or six-digit colour.

## Adding a theme

1. Copy the closest theme, change `name`, `label` and `when`.
2. Pick the palette from the brand book, then check it: `python tools/theme_apply.py x.pptx --theme my_theme --check`.
3. Tune `size` upward if the room is large; never below the floors.
4. Run `python tools/deck_qa.py examples/data-layer.example.json --theme my_theme`.
5. Add one line per theme to the table at the top of this file.

A theme is a palette, not a design: it will not fix a slide with six bullets, and it is not
meant to. Structure is `assets/layouts.json`, copy is the deck itself.
