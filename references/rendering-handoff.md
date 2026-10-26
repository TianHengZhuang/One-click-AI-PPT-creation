# Rendering handoff

The last mile: turn a finished deck payload into a `.pptx` file.

This step is **optional and off by default**. The skill's contract is still the outline (Markdown) plus, when asked, the structured payload in `references/output-contract.md`. Rendering only makes sense once the content is stable — never render to fix a deck that is still being written.

## When to use it

- The user asks for a real PowerPoint file (`.pptx`), not just slide text.
- The pack must land inside a corporate template so branding, fonts and masters apply.
- The deck already exists as `references/output-contract.md` JSON and the user wants an editable starting file.

Do **not** use it to skip the workflow: Step 1–4 (clarify → structure → outline → write) still produce the content. The renderer is a formatting step, not an authoring step.

## Inputs

| Input | Role | Required |
|-------|------|----------|
| `<deck>.json` | Deck payload in the output contract (`schema_version` `"1.0"` or `"1.1"`, `meta` + `slides`) | yes |
| `--template <file>.pptx\|.potx` | Corporate template supplying slide masters | no (defaults to the bundled Office master) |
| `--master-map <file>.json` | Explicit layout + placeholder mapping for that template | no (auto-resolved, see `references/master-mapping.md`) |
| `--out <path>.pptx` | Output file | no (naming convention below) |

The payload is the canonical source. A Markdown deck alone cannot be rendered — emit the JSON twin first (SKILL.md Step 5), then run `tools/deck_lint.py` so both copies agree before rendering.

## Workflow

1. **Emit the payload.** Ask for JSON if the user has not already asked; keep the Markdown deck as the human copy.
2. **Lint the pack.** `python tools/deck_lint.py <pack-base>` must exit 0. Fix any hard gate before rendering.
3. **Render.**
   ```bash
   python tools/render_pptx.py examples/status-report.json
   python tools/render_pptx.py examples/status-report.json --template acme-deck.potx --master-map acme-master-map.json
   python tools/render_pptx.py examples/status-report.json --check        # dry run, no file written
   ```
4. **Verify.** Open the file, confirm the layout mapping report has no fallbacks, and check the first and last slide by hand.

## What the renderer does

- One `.pptx` slide per payload slide, in order.
- Slide 1 uses the **title** role (deck title + `audience · purpose · ~est_minutes min` subtitle).
- Every other slide uses the **content** role: headline into the title placeholder, `bullets` into the body placeholder.
- `speaker_notes` go into the PowerPoint notes pane, followed by a `Visual: …` line so the suggested chart or diagram is not lost.
- Layout roles are resolved against the template by name, then by keyword, then by index (see `references/master-mapping.md`).

### Layers

Slides with a `chart` or `table` block are laid out in four bands, top to bottom. The
copy zone and the data zone split the body; they never overlap, and nothing enters the
headline or footnote band.

| Layer | Band | Content |
|-------|------|---------|
| `headline` | top, ~1.05 in | slide headline from the template title placeholder |
| `copy` | body left (full width when there is no data block) | `bullets`, capped at 3 beside a data block |
| `data` | body right, ~56% of body width | one native chart or table |
| `footnote` | bottom strip | `Source: …` from `chart.source` / `table.source` |

Widths are computed from the actual slide size, so a 4:3 template is not overrun.
Charts are inserted as real PowerPoint chart objects (editable data, `type`, `series`
and `emphasis` preserved); tables are real table shapes with the header row bolded at
12 pt. Nothing is rasterised.

When a data block cannot be drawn — python-pptx rejects the type, or the slide sits on
a template whose body placeholder cannot be resized — the renderer keeps the copy,
drops the block, and records the reason in `warnings`. The deck never fails to export
because of a chart.

`--json` returns `slides[].layers` (`{"copy": 3, "data": "chart:bar", "footnote": "…"}`)
so a caller can confirm which layer each slide received.

## What the renderer does not do

- It does not draw free-form diagrams, screenshots or SmartArt. Only the structured `chart` / `table` blocks become objects; any other `visual` stays a text cue in the notes for the human to place.
- It does not restyle copy. Headline and bullet wording goes in as written — the copywriting rules were already applied upstream.
- It does not fix timing. If `meta.est_minutes` drifts from `meta.target_minutes`, trim notes or drop a slide first.
- It does not overwrite silently: an existing output file is never replaced unless `--force` is passed.

## Output naming

Follows `references/export-checklist.md`:

```
{deck-slug}_{version}_{YYYYMMDD}.pptx            # single slot
{deck-slug}_{version}_{slot}min_{YYYYMMDD}.pptx   # duration-scaled packs (3 / 8 / 15)
```

`{deck-slug}` is derived from `meta.title`; pass `--version` (default `v1.0.0`) and `--slot` when the pack is scaled by length.

## Dependencies

`python-pptx` is the only third-party dependency and it is **not** required for the skill itself — the checker `tools/deck_lint.py` remains standard library only. When the module is missing, the renderer exits with code 2 and prints the install line:

```bash
pip install python-pptx
```

If the user cannot install packages, stay on the no-dependency path: hand over the Markdown deck and the JSON payload, and note that rendering was skipped.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `layout fallback` warnings | Template layout names differ (localised masters) | Add the template's real names or keywords to the master map |
| Title or body text missing | Placeholder indices differ from the default | Map `placeholders.title` / `placeholders.body` explicitly |
| Chinese bullets look cramped | Template body default is too small | Raise the body size in the template, or apply `references/zh-cn-adaptation.md` type sizes |
| Notes pane empty | Payload slide has no `speaker_notes` | Fix the payload; `deck_lint` treats empty notes as an error |
| Rendered file rejected by brand review | Template not applied | Pass `--template` with the corporate master |
| Chart or table missing on a slide | Block dropped; read `warnings` in the `--json` report | Fix the block (see the limits in `references/output-contract.md`) or drop it and keep the `visual` cue |
| Chart area looks squeezed | Bullets left over from a text-only draft | Keep 3 bullets beside a data block; move detail to the notes |

## Hand-off checklist

- [ ] Payload validates (`python tools/render_pptx.py <payload> --check`).
- [ ] `deck_lint` exits 0 on the pack.
- [ ] Layout mapping report shows the expected role for every slide (no unintended fallbacks).
- [ ] `slides[].layers` in the `--json` report lists the data layer you expected, and `warnings` is empty.
- [ ] File name follows the export convention.
- [ ] The `.pptx` opens and slide 1 / last slide are visibly correct.
