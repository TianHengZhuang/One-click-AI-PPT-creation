# Changelog

## v2.0.0 (2026-10-26)

### Added
- `tools/source_extract.py` — condenses attached source material (PDF, Word, spreadsheets, PowerPoint, Markdown, CSV/TSV, plain text, folders) into one `source-brief.json`: sections, addressable chunks (`file.pdf#3`), tables and deduplicated numbers with context; a single unreadable file never stops the run; standard library only, binary formats need `pypdf` / `python-docx` / `python-pptx` / `openpyxl` and fall back with an install hint when missing
- `references/source-brief.md` — when to run the extractor, every flag, what the brief holds, how chunk ids are referenced from slides
- `tools/render_pptx.py` — optional `chart` / `table` blocks (schema 1.1) now render as native PowerPoint objects instead of notes text: `type` / `categories` / `series` / `unit` / `emphasis` become a real chart (eight families incl. stacked bar and pie), `columns` / `rows` become a real table; both carry `source` into a footnote band. Data slides are laid out in four non-overlapping bands (headline, copy, data, footnote) sized from the actual slide width, so a 4:3 template is not overrun and bullets cap at 3 beside a data block. A block that cannot be drawn is dropped with a reason in `warnings` rather than failing the export; `--json` reports `slides[].layers`
- `references/output-contract.md` — schema 1.1 data layer: field tables for `chart` and `table`, limits (2–12 categories, 1–4 series, 2–6 columns, 8 rows), one-block-per-slide and not-on-the-title-slide rules, a worked example, and four new validation checklist items
- `examples/data-layer.example.json` — six-slide status deck with two charts, a stacked-bar comparison and an issues table
- `tests/test_render_pptx.py` — 24 cases covering schema 1.0/1.1 acceptance, chart and table limits, the one-data-layer-per-slide rule, layer geometry (no overlap, footnote band untouched, 4:3 containment) and, when `python-pptx` is installed, native chart/table smoke renders
- `tests/test_source_extract.py` — 26 cases covering chunk ids, table extraction, number regexes (grouped thousands, trailing punctuation, version strings) and CLI exit codes
- `assets/layouts.json` — layout library: fourteen slide roles in 31 variants, each with a `when` line, four bands (headline, copy, data, footnote) in inches on a 16:9 canvas, and copy limits (`bullets`, `words_per_bullet`, `headline_words`, `data`); data only, no image, no python-pptx
- `assets/themes/` — three themes as JSON palettes plus type scale: `consulting` (navy ink, blue accent), `swiss` (black on white, one red accent), `editorial` (warm paper, serif headlines, brick accent)
- `tools/theme_apply.py` — re-skins an existing `.pptx` to a bundled theme: slide background, title/body/table type, chart series colours, table header fill and cell type; geometry untouched, so a designer's layout survives and a deck can be re-themed; `--list`, `--check`, `--out`, `--force`, `--json`; rejects a palette that breaks a contrast floor rather than shipping unreadable text
- `tools/deck_qa.py` — pure standard-library visual QA on a payload: headline length and honesty, bullet count and length, figures with no chart, notes pace against `est_seconds`, chart and table load, repeated openers, theme contrast; fourteen rules QA101-QA114, 0-100 score with a letter grade, `--strict`, `--json`, `--report`, exit codes for CI
- `references/layout-library.md` — canvas, role and variant table with copy budgets, band geometry, how the library relates to the renderer, how to add a variant
- `references/themes.md` — the three themes, every field of a theme file, the contrast floors and why each one exists, how to add a palette
- `references/visual-qa.md` — every QA rule with severity and trigger, the scoring model, how to read and fix a report, when to run it, how it differs from `deck_lint.py` and `deck_review.py`
- `examples/qa-report.example.md` — worked QA report on `examples/status-report.json` (80/100, four warnings, four notes)
- `tests/test_deck_qa.py` — 55 cases covering text weighting, number scanning (dates, years and single digits excluded), layout limits, role inference, every QA rule, theme contrast, scoring and CLI exit codes
- `tests/test_theme_apply.py` — 34 cases covering colour maths, contrast checks, theme resolution, CLI behaviour and, when `python-pptx` is installed, re-skinning runs

### Changed
- README.md — helper-script count, tools tree and reference tree list the extractor and the brief
- SKILL.md — Step 0 condenses attached material into `source-brief.json` before the deck is drafted; Step 3 closes every slide purpose with the chunks it draws on; Step 4 drops any number that is in neither the brief nor the user's message; the tools index and edge cases cover attached sources
- `tools/render_pptx.py` — accepts `schema_version` `"1.0"` and `"1.1"`; rendering is unchanged for text-only payloads
- `tools/deck_lint.py` — accepts schema 1.1 and hard-gates the data layer: `json-data-layer` fires when a slide carries both a chart and a table, when a data block sits on slide 1, or when either block is not an object
- `assets/layouts.json` — `headline_words` filled in for the variants that lacked it, so every role has a headline budget for the QA pass
- README.md — helper count, assets/tools/references/examples trees, a "Check the slides" section and a "Theme a deck" section
- SKILL.md — Step 2 picks slide roles from the layout library, Step 4 sizes copy to the role's budget, Step 5 runs the QA pass before hand-off, the tools index and edge cases cover theming and QA
- `references/rendering-handoff.md` — new "Layers" section (band table, chart/table fidelity, degradation to `warnings`, `layers` in the `--json` report), updated "does not do", two troubleshooting rows and one hand-off checklist item

### Fixed
- `tools/source_extract.py` — chunk ids restarted at `#1` in every section, so a document with several sections produced duplicate ids and a cited chunk could not be resolved; numbering now runs across the whole document
- `tests/test_source_extract.py` — a case pins chunk id uniqueness across sections

## v1.9.0 (2026-10-21)

### Added
- `references/slide-structures.md` — five scene-specific structures: 17 Academic defense, 18 Crisis communication, 19 Seed / early-stage fundraise, 20 Sales demo / proof of concept, 21 Conference keynote; the "Choosing a structure" table extended to match
- `examples/crisis-comms.md` — worked 8-slide crisis communication deck on a platform outage

### Changed
- SKILL.md — Step 2 now selects from 21 structures; the examples index lists the crisis-comms deck
- README.md — structure tree and example table list the new structure count and the crisis-comms sample

## v1.8.0 (2026-10-14)

### Added
- `tools/deck_review.py` — audits a deck that already exists (Markdown or output-contract JSON): hard gates, warnings, a 0-100 score across structure / copy / evidence / delivery, and a READY / REVISE / REWRITE verdict; `--slot`, `--min-score`, `--strict`, `--json`, `--out` and `--quiet`; Chinese decks are reviewed in characters per minute; standard library only
- `references/deck-review.md` — what the review checks, every finding code, the scoring model, the Chinese rules, and how the review complements `tools/deck_lint.py`
- `references/audience-simulation.md` — the pre-delivery stress test: pick two or three seats, ask their questions against the slides, mark answered / partial / gap, recommend the smallest fix set
- `examples/deck-review.example.md` — worked review of `examples/status-report.md`
- `examples/audience-simulation.example.md` — worked three-seat simulation of the same deck

### Changed
- SKILL.md — Step 5 routes an existing deck through `tools/deck_review.py` instead of rewriting it blind, and adds the audience-simulation pass before a decision meeting; edge cases, tools and examples index updated
- README.md — structure tree, reference table, example table and a "Review an existing deck" section

## v1.7.0 (2026-09-22)

### Added
- `tools/render_pptx.py` — renders an output-contract payload to a `.pptx`, into the bundled Office master or a corporate template (`--template` + `--master-map`); `--check` resolves every layout without writing a file, `--json` prints the resolution report
- `references/rendering-handoff.md` — render workflow, inputs and outputs, file naming, `python-pptx` dependency and troubleshooting
- `references/master-mapping.md` — corporate master layout/placeholder mapping, name → keyword → index resolution order, localization notes
- `examples/master-map.example.json` — worked master map for the bundled master

### Changed
- SKILL.md — Step 5 routes `.pptx` requests through the renderer; the edge-case list and reference index updated
- README.md — structure tree, reference table and a "Render to .pptx" section


## v1.6.0 (2026-09-18)

### Added
- deck_lint: speaker_notes hard/soft gates (empty is error; short/long/few-lines warn)
- references/duration-scaling.md — 3 / 8 / 15 minute slide + notes budgets and export naming
- SKILL.md routes duration scaling before multi-slot export


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
