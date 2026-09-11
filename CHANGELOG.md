# Changelog

All notable changes to One-Click AI PPT.

## [v1.2.0] - 2026-09-11

### Added

- `references/output-contract.md` — optional JSON/YAML schema (`meta` + `slides`), validation checklist, and speaker-note timing model (130 wpm en / 240 chars per min zh-CN, +8s per slide)
- `examples/status-report.json` — structured payload for the existing status-report deck

### Changed

- `SKILL.md` — Step 5 now routes structured/rendering requests through the output contract; examples section lists the JSON sample
- `README.md` — structure tree, reference index, and examples table include the contract and JSON sample

## [v1.1.0] - 2026-09-11

### Added

- `references/design-guide.md` — layout, type scale, colour and chart selection
- `references/zh-cn-adaptation.md` — fonts, type size, punctuation, tone and delivery for Chinese decks
- `examples/status-report.md`, `examples/investor-update.md`, `examples/training.md` — three fully worked decks
- Reference index and examples table in `README.md`

### Changed

- `references/slide-structures.md` — expanded from 10 to 16 structures, plus a "Choosing a structure" table
- `SKILL.md` — design guidance now defers to the design guide; added a language section and two edge cases

## [v1.0.0] - 2026-09-11

### Added

- `SKILL.md` — the skill: clarify, pick a structure, draft the outline, write each slide, format the output
- `references/slide-structures.md` — 10 deck structures by purpose, with rules of thumb
- `references/copywriting-guide.md` — copy rules, before/after table, speaker-note guidance
- `README.md` — what it does, install paths per client, usage, full example output
- `LICENSE` — MIT
