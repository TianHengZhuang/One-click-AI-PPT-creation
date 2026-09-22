# Slide master mapping

How a deck payload finds the right layout and placeholders inside a corporate PowerPoint template.

Slide masters are the reason a rendered deck looks like it belongs to the company: the template defines which layouts exist (`Title Slide`, `Title and Content`, `Section Header`, …) and where the title, body, date and footer placeholders sit. `tools/render_pptx.py` resolves each payload slide to one of those layouts.

## Layout roles

The renderer only needs four roles. Each payload slide is assigned one:

| Role | Used for | Typical layout name |
|------|----------|---------------------|
| `title` | Slide 1 — deck title | `Title Slide`, `Title`, `封面` |
| `content` | All body slides | `Title and Content`, `Title, Content`, `标题和内容` |
| `section` | Optional section divider slides | `Section Header`, `Section Title`, `节标题` |
| `closing` | Optional final / Q&A slide | `Title Only`, `Blank`, `Closing` |

`section` and `closing` are optional: without them, dividers and the closing slide render as `content`.

## Resolution order

For every role, the renderer tries these steps in order and records which one matched:

1. **Explicit name** — `layouts.<role>.name`, matched case-insensitively against the template's layout names.
2. **Keywords** — `layouts.<role>.keywords[]`, matched as substrings, so a template in any language still resolves (`["content", "内容", "contenu"]`).
3. **Index** — `layouts.<role>.index`, the 0-based position in `prs.slide_layouts`.
4. **Built-in default** — `0` for `title`, `1` for `content`. This emits a `layout fallback` warning and should be fixed for brand-critical decks.

Placeholders resolve the same way, top-down:

1. `layouts.<role>.placeholders.title` / `.body` — an explicit placeholder index (`placeholder_format.idx`).
2. The first placeholder of the matching type (`TITLE` / `BODY`) in that layout.
3. If no body placeholder exists, the renderer adds a text box below the title and warns.

## Mapping file

```json
{
  "version": "1.0",
  "name": "Acme corporate master",
  "layouts": {
    "title":   { "name": "Title Slide",       "index": 0, "placeholders": { "title": 0, "subtitle": 1 } },
    "content": { "name": "Title and Content",  "index": 1, "placeholders": { "title": 0, "body": 1 } },
    "section": { "keywords": ["section", "divider", "节"], "index": 2 },
    "closing": { "keywords": ["title only", "blank"],      "index": 5 }
  }
}
```

A worked sample ships as `examples/master-map.example.json`.

### Fields

| Field | Type | Notes |
|-------|------|-------|
| `version` | string | Mapping schema version, currently `"1.0"` |
| `name` | string | Human label for the mapping, shown in the render report |
| `layouts.<role>.name` | string | Exact layout name in the template |
| `layouts.<role>.keywords` | string[] | Substring candidates; lower-case match |
| `layouts.<role>.index` | integer | 0-based `slide_layouts` position |
| `layouts.<role>.placeholders.title` | integer | `placeholder_format.idx` for the headline |
| `layouts.<role>.placeholders.subtitle` | integer | Sub-title placeholder (title role only) |
| `layouts.<role>.placeholders.body` | integer | Bullet body placeholder |

Only `layouts` is required; every role and every field inside it is optional.

## Localised masters

Corporate templates ship localised layout names. Keyword lists keep one mapping file working across them:

| Locale | Title layout | Content layout |
|--------|--------------|----------------|
| `en-US` | Title Slide | Title and Content |
| `zh-CN` | 标题幻灯片 | 标题和内容 |
| `fr-FR` | Diapositive de titre | Titre et contenu |
| `de-DE` | Titelbild | Titel und Inhalt |

A mapping tuned for a Chinese template:

```json
{
  "version": "1.0",
  "name": "Chinese corporate master",
  "layouts": {
    "title":   { "keywords": ["封面", "标题幻灯片", "title slide"] },
    "content": { "keywords": ["标题和内容", "title and content"], "placeholders": { "body": 1 } },
    "closing": { "keywords": ["结束", "thanks", "q&a"] }
  }
}
```

## Checking a template before a real render

```bash
python tools/render_pptx.py <payload>.json --template acme.potx --master-map acme.json --check
```

`--check` prints the layout inventory of the template plus the resolved role → layout table and the per-slide assignment, then exits without writing a file. Run it once per template; the same mapping then works for every deck.

## Notes

- `--master-map` is only meaningful together with `--template`. Without a template the bundled Office master is used and the built-in defaults apply.
- Keep the mapping file in the repository next to the template; it is the record of which corporate layout each role points at.
- If a template changes, re-run `--check`: a renamed layout silently degrades to the keyword or index step otherwise.
