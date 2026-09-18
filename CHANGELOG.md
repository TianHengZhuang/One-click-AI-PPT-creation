# Changelog

## v1.5.1 (2026-09-18)

### Added
- Export checklist: deliverable file naming {deck-slug}_{version}_{YYYYMMDD}.{ext} so re-exports never overwrite silently


All notable changes to One-Click AI PPT.

## [v1.5.0] - 2026-09-14

### Added

- references/executive-one-pager.md — one-page leave-behind spec (situation, key numbers, single ask, risks, next steps) with hard no-new-facts rule and quality gate
- SKILL.md — Optional Step 6 routes one-pager / leave-behind requests after the deck is stable

### Changed

- README.md — reference index includes the one-pager guide

## [v1.4.2] - 2026-09-13

### Added

- `tools/deck_lint.py` — optional, standard-library-only checker for a multi-artifact deck pack: slide counts, headlines, timing math, note budgets and repeated numeric claims are cross-checked across the Markdown, JSON, notes and HTML copies; hard gates and soft warnings are reported separately and the exit code is CI-friendly
- `README.md` — structure tree and a "Validate a deck pack" section
- `SKILL.md` — Step 5 runs the lint before hand-off when a pack ships as more than one artifact
- `references/export-checklist.md` — the deliverable pack section names the lint run

### Fixed

- `examples/status-report.json` — `meta.target_minutes` was 8 while the notes budget rolls up to 4.8 minutes; now 5, with the Markdown request line and the notes header following

## [v1.4.1] - 2026-09-12

### Fixed

- `SKILL.md` Examples section listed only Markdown + JSON samples after v1.3/v1.4 added HTML and rehearsal notes. Now lists all four status-report artifacts.

## [v1.4.0] - 2026-09-12

### Added

- `references/rehearsal-notes.md` — speaker-only notes pack convention (say / watch-for, timing, pack layout)
- `examples/status-report-notes.md` — status-report talk track aligned with the existing deck

### Changed

- `SKILL.md` — Step 5 routes rehearsal / speaker-only requests through the notes pack
- `README.md` — structure tree, reference index, examples table

## [v1.3.0] - 2026-09-12

### Added

- `references/export-checklist.md` — hard/soft gates before hand-off: slide count, type size, contrast, chart labels, speaker-note budget, deliverable pack
- `references/html-export.md` — single-file offline HTML deck convention (tokens, keyboard nav, print, a11y)
- `examples/status-report.html` — status-report deck as a presentable HTML file

### Changed

- `SKILL.md` — Step 5 routes offline HTML requests and requires the export checklist before hand-off
- `README.md` — structure tree, reference index, examples table

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
