# Roadmap

One-Click AI PPT evolution plan.

## In progress — v2.0.0 (unreleased)

- `tools/source_extract.py` — attached material condensed into one `source-brief.json`, with addressable chunks cited from the slides
- `tools/render_pptx.py` — native charts and tables, laid out in four bands per slide (schema 1.1)
- `tools/evidence_lint.py` — citations checked against the source brief
- `assets/layouts.json` — layout library: fourteen roles, 31 variants, copy budgets
- `assets/themes/` + `tools/theme_apply.py` — three palettes, applied to an existing `.pptx` without touching geometry
- `tools/deck_qa.py` — visual QA before hand-off: density, notes pace, chart/table load, contrast
- References for each: `source-brief.md`, `output-contract.md` (schema 1.1), `layout-library.md`, `themes.md`, `visual-qa.md`

Each slice lands in `release/v2.0.0` on its own branch and merges to `main` as one release.

## Released

### v1.9.0 — Scene-Specific Deck Structures (2026-10-21)

- `references/slide-structures.md` — five new structures: academic defense, crisis communication, seed / early-stage fundraise, sales demo / proof of concept, and conference keynote, with the "Choosing a structure" table extended
- `examples/crisis-comms.md` — worked crisis communication deck on a platform outage

### v1.8.0 — Deck Review and Audience Simulation (2026-10-14)

- `tools/deck_review.py` — audits an existing deck against the skill's rules: hard gates, warnings, a structure / copy / evidence / delivery score and a READY / REVISE / REWRITE verdict, in English or Chinese
- `references/deck-review.md` — the checks, the finding codes and the scoring model
- `references/audience-simulation.md` — a seat-by-seat stress test before a decision meeting
- `examples/deck-review.example.md`, `examples/audience-simulation.example.md` — worked samples on the status-report deck

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

No committed scope for the next release. Candidate ideas are tracked in issues.
