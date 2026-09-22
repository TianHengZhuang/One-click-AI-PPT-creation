# Roadmap

One-Click AI PPT evolution plan.

## Released

### v1.7.0 — Rendering Handoff (2026-09-22)

- `tools/render_pptx.py` — renders an output-contract payload to a `.pptx`, into the bundled Office master or a corporate template
- `references/rendering-handoff.md` — render workflow, inputs and outputs, file naming, dependency and troubleshooting
- `references/master-mapping.md` — corporate master layout/placeholder mapping, resolution order, localization notes
- `examples/master-map.example.json` — worked master map; `--check` resolves every layout without writing a file

### v1.5.0 — Executive One-Pager (2026-09-14)

- references/executive-one-pager.md: leave-behind page contract synced to deck numbers
- Optional SKILL Step 6 for sponsors who will not attend the talk

### v1.0.0 — Core Skill (2026-09-11)

- Five-step workflow: clarify → structure → outline → write → format
- 10 deck structures by purpose
- Copywriting guide with before/after examples
- Design guidance for on-slide layout in SKILL.md
- MIT license

### v1.1.0 — Reference Depth (2026-09-11)

- `references/design-guide.md` — layout, type scale, colour, chart selection
- `references/zh-cn-adaptation.md` — Chinese-language adaptation
- `references/slide-structures.md` expanded to 16 structures with a selection table
- `examples/` — three worked decks: status report, investor update, training
- Reference index and examples table in README

### v1.2.0 — Format Outputs (2026-09-11)

- `references/output-contract.md` — optional structured output (JSON/YAML) with `meta` + `slides`
- Speaker-note timing model (130 wpm English / 240 chars per min Chinese, +8s slide overhead)
- `examples/status-report.json` — worked structured payload
- SKILL Step 5 routes machine-readable requests through the contract

## Planned

### Long-Term

- Deck review mode: audit an existing deck against the skill's rules
- Audience-simulation pass before delivery
