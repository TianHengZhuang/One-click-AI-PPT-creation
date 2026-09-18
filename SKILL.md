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

## Workflow

### Step 1 — Clarify (ask only if truly missing)

Ask for: target audience, time limit (5/10/20 min), desired number of slides (default 10), and purpose (inform / persuade / pitch / report). If the user just says "make me a deck about X", proceed with sensible defaults: 10 slides, business audience, persuasive-informative mix. Do not block on questions the user already answered.

### Step 2 — Pick a structure

Choose from the 16 structures in references/slide-structures.md, or use its "Choosing a structure" table. Default: the 10-slide Business Pitch. Match the structure to the purpose:

- Pitch / proposal → Problem → Solution → Market → Traction → Ask
- Status report → Wins → Metrics → Issues → Next steps
- Training / explainer → Concept → Why it matters → How it works → Examples → Practice

### Step 3 — Draft the outline

Produce a numbered slide list. Each slide gets a working title (a full sentence, not a noun phrase) and a one-line purpose.

### Step 4 — Write each slide

For every slide output:

- **Headline**: a claim or takeaway, not a label ("Q3 revenue grew 18% on enterprise renewals", not "Revenue").
- **3–5 bullet points max**, each under 12 words.
- **One visual suggestion** per slide (chart, diagram, screenshot, icon).
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
- User brings an existing deck to fix: audit it against the copywriting rules and return a corrected outline, keeping their own content.
- User wants a real .pptx file: provide the full outline plus slide text in a format they can paste into PowerPoint/Keynote/Google Slides, and offer the structure for a rendering script.

## Examples

Worked decks live in examples/: examples/status-report.md, examples/investor-update.md, examples/training.md.
Structured payload sample: examples/status-report.json.
Offline HTML sample: examples/status-report.html.
Rehearsal talk track sample: examples/status-report-notes.md.
Pack checker: tools/deck_lint.py (optional, standard library only).

---

# Optional Step 6 — Executive One-Pager

When the user asks for a leave-behind, email summary, or one-pager **after** the deck is stable, follow `references/executive-one-pager.md`.

- Do not invent numbers that are not in the deck  
- Keep a single ask  
- Match deck language  
