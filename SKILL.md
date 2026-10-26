---
name: one-click-ai-ppt
description: Turn any topic into a complete business presentation — outline plus slide-by-slide speaker notes. Use when the user asks to create, generate, or draft a PPT, PowerPoint, slide deck, pitch deck, or presentation, or says "make me slides" / "give me a deck".
---

# One-Click AI PPT

Build a complete, presentation-ready business deck from a single topic. No external tools, no API keys — just structured thinking.

## When to use

- User asks for a PPT / PowerPoint / slide deck / pitch deck / presentation.
- User has a topic but no structure.
- User needs speaker notes or talking points for each slide.
- User attaches a report, spreadsheet, deck or notes the deck must be built from.

## Workflow

### Step 0 — Read the source first (only when material is attached)

When the request comes with files — a PDF, a Word document, a spreadsheet, a slide deck, a folder of notes — condense them into one brief before drafting anything:

```bash
python tools/source_extract.py <files-or-folders> --out source-brief.json
```

Draft from `source-brief.json`, not from a skim of the attachments. The brief holds sections, addressable chunks (`report.pdf#3`), tables, and deduplicated numbers with the sentence around each one; every field is described in `references/source-brief.md`. Add `--recursive` for folders, `--max-chars` to trim long documents.

If the extractor cannot run — no Python, or a binary format whose parser is missing — say so in one line, read the files directly, and keep the same discipline by hand: note the section each number came from. A single unreadable file is not a reason to stop; skip it and name it in the hand-off.

No attachments? Skip this step and go to Step 1.

### Step 1 — Clarify (ask only if truly missing)

Ask for: target audience, time limit (5/10/20 min), desired number of slides (default 10), and purpose (inform / persuade / pitch / report). If the user just says "make me a deck about X", proceed with sensible defaults: 10 slides, business audience, persuasive-informative mix. Do not block on questions the user already answered.

### Step 2 — Pick a structure

Choose from the 21 structures in references/slide-structures.md, or use its "Choosing a structure" table. Default: the 10-slide Business Pitch. Match the structure to the purpose:

- Pitch / proposal → Problem → Solution → Market → Traction → Ask
- Status report → Wins → Metrics → Issues → Next steps
- Training / explainer → Concept → Why it matters → How it works → Examples → Practice

Once the story is chosen, pick the slide roles from the layout library — `assets/layouts.json`, fourteen roles in 31 variants, each with a `when` line and a copy budget. Choose the role by the job the slide does (a `chart` slide with no chart is a bullet slide in the wrong role), and take its `limits` as the budget for the copy in Step 4. Geometry, roles and the bands are described in `references/layout-library.md`.

### Step 3 — Draft the outline

Produce a numbered slide list. Each slide gets a working title (a full sentence, not a noun phrase) and a one-line purpose.

When a `source-brief.json` exists, close each purpose line with the chunks the slide draws on: `(evidence: report.pdf#3, report.pdf#5)`. A slide with no chunk behind it is a slide with no source — keep it only as a transition or a section break. If the brief has no chunk that supports a slide you wanted, that is a gap in the source: drop the slide or ask the user for the missing material.

### Step 4 — Write each slide

For every slide output:

- **Headline**: a claim or takeaway, not a label ("Q3 revenue grew 18% on enterprise renewals", not "Revenue").
- **3–5 bullet points max**, each under 12 words — or the tighter budget of the slide's role in `assets/layouts.json` when it has one. Copy that overflows its band is flagged by `tools/deck_qa.py`, not silently shrunk.
- **Numbers you can point at**: every figure in a headline or bullet must appear in `source-brief.json` or in the user's own message. If it is in neither, drop the number or mark the gap — never round it into something plausible.
- **One visual suggestion** per slide (chart, diagram, screenshot, icon). When the point is a number comparison the audience should read at a glance, ship it as a structured `chart` or `table` block in the payload too (schema 1.1, limits in `references/output-contract.md`) — the renderer turns it into a native object; keep the `visual` line regardless, it is the Markdown fallback.
- **Speaker note**: 2–3 sentences the presenter can say out loud.

### Step 5 — Format the output

Use this Markdown template:

```
# <Deck title> (<N> slides, ~<M> min)

## Slide 1 — <Headline>
- ...
- ...
Visual: ...
Notes: ...

## Slide 2 — <Headline>
...
```

If the user wants a different format (table, plain text), follow their request.

If the user asks for JSON, YAML, a machine-readable outline, or a payload for a rendering script, emit the structured contract in `references/output-contract.md`. Keep the same slide content as the Markdown form; add `est_seconds` per slide using that file's timing model, and put the roll-up in `meta.est_minutes`. A worked sample is `examples/status-report.json`.

If the user asks for an offline presentable file, emit a single-file HTML deck per `references/html-export.md`. Before any export, run `references/export-checklist.md` and report hard-gate failures.

When the same talk must ship at **3 / 8 / 15 minutes**, follow `references/duration-scaling.md`: cut or add slides, keep one message per slide, and name exports `{slug}_{version}_{slot}min_{date}`. Run `tools/deck_lint.py` on each scaled pack.

If the user asks for a rehearsal script, speaker-only notes, or a talk track, emit `references/rehearsal-notes.md` (expand JSON `notes` into speakable paragraphs; do not invent a second storyline). Worked sample: `examples/status-report-notes.md`.

If the pack ships as more than one artifact (Markdown plus JSON, notes and/or HTML), run `python tools/deck_lint.py <deck-path>` before hand-off. It cross-checks slide counts, headlines, timing and numbered claims across the copies and reports hard-gate failures and soft warnings. Worked sample: `python tools/deck_lint.py examples/status-report`.

If a deck already exists — the user brings one to review, or you just wrote one — audit it before touching the copy: `python tools/deck_review.py <deck-path>` reports the hard gates that block a hand-off, the warnings worth a look, a 0-100 score across structure / copy / evidence / delivery and a READY / REVISE / REWRITE verdict. Add `--slot <minutes>` to check the deck against a time slot, `--json` for a machine-readable report, and `--min-score` / `--strict` to make the run fail when it should. Rules and finding codes: `references/deck-review.md`. Worked sample: `examples/deck-review.example.md`.

Before a decision meeting, stress-test the deck against the room using the seat-by-seat pass in `references/audience-simulation.md`: pick two or three seats, ask each seat's questions against the slides, mark every answer answered / partial / gap, then recommend the smallest set of additions. Worked sample: `examples/audience-simulation.example.md`.

Before hand-off, ask whether the slides will work in a room: `python tools/deck_qa.py <payload>.json` checks density, headlines, notes pace, table and chart load, and — with `--theme` — whether the palette is readable; `--strict` makes warnings fail, `--json` and `--report <file>.md` write a report. Rules and scoring: `references/visual-qa.md`; worked report: `examples/qa-report.example.md`. Fix errors first, then over-long copy, then density; do not shrink type to win a point.

If the user asks for a real `.pptx` file, follow `references/rendering-handoff.md`: emit the structured payload first, lint the pack, then run `python tools/render_pptx.py <payload>.json`. Add `--template <corporate>.potx --master-map <map>.json` to land the deck in a corporate slide master (see `references/master-mapping.md`), and `--check` to resolve every layout without writing a file. The renderer needs `python-pptx`; if it cannot be installed, hand over the Markdown deck plus the payload instead.

## Copywriting rules

- Write in active voice. "We cut onboarding time by 40%", not "Onboarding time was reduced".
- Numbers first: lead with the metric, then the context.
- One idea per bullet. No nested bullets.
- Keep every sentence under ~15 words.
- No jargon the audience wouldn't use themselves.
- See references/copywriting-guide.md for before/after examples.

## Design guidance (pass along to the user)

- One message per slide; if a slide needs more than 5 bullets, split it.
- High-contrast text on a light background; avoid dark gradients.
- 24pt+ body text, 36pt+ headlines.
- Use one accent color for calls-to-action and key numbers.
- Charts beat tables; tables beat paragraphs.
- See references/design-guide.md for layout, type scale, colour and chart selection.

## Language

Write in the language the user asks for. When the output is Chinese, also apply references/zh-cn-adaptation.md: larger type, full-width punctuation, conclusion-first headlines, no four-character filler.

## Edge cases

- Topic is vague ("something about marketing"): propose 3 concrete angles and let the user pick.
- User wants another language: write in that language, keep the same structure. For Chinese, apply references/zh-cn-adaptation.md.
- User attaches a report, data file or notes: run Step 0 first, then draft from the brief; quote no figure the brief does not contain.
- User brings an existing deck to fix: run `tools/deck_review.py` on it, fix the hard gates and the flagged copy, and return a corrected outline, keeping their own content and message.
- User has a finished deck that looks off: theme it before redesigning it — `python tools/theme_apply.py deck.pptx --theme consulting|swiss|editorial`, then re-run `tools/deck_qa.py` on the payload; a palette will not fix six bullets.
- User wants a real .pptx file: provide the full outline plus slide text in a format they can paste into PowerPoint/Keynote/Google Slides, and offer the structure for a rendering script.

## Examples

Worked decks live in examples/: examples/status-report.md, examples/investor-update.md, examples/training.md, examples/crisis-comms.md.
Structured payload sample: examples/status-report.json.
Offline HTML sample: examples/status-report.html.
Rehearsal talk track sample: examples/status-report-notes.md.
Pack checker: tools/deck_lint.py (optional, standard library only).
Deck review: tools/deck_review.py (optional, standard library only); worked report: examples/deck-review.example.md.
Audience simulation: references/audience-simulation.md; worked pass: examples/audience-simulation.example.md.
Renderer (optional, needs python-pptx): tools/render_pptx.py — payload to .pptx, with corporate master mapping.
Source extract: tools/source_extract.py (optional, standard library only; PDF / Word / PowerPoint / Excel need pypdf, python-docx, python-pptx or openpyxl) — attached material to one source-brief.json; what the brief holds: references/source-brief.md.
Master map sample: examples/master-map.example.json.
Layout library: assets/layouts.json (14 roles, 31 variants, copy budgets); reference: references/layout-library.md.
Themes: assets/themes/{consulting,swiss,editorial}.json; `python tools/theme_apply.py <deck>.pptx --theme swiss` restyles an existing file (needs python-pptx); reference: references/themes.md.
Visual QA: tools/deck_qa.py (optional, standard library only) — will these slides work in a room; rules: references/visual-qa.md; worked report: examples/qa-report.example.md.

---

# Optional Step 6 — Executive One-Pager

When the user asks for a leave-behind, email summary, or one-pager **after** the deck is stable, follow `references/executive-one-pager.md`.

- Do not invent numbers that are not in the deck  
- Keep a single ask  
- Match deck language  
