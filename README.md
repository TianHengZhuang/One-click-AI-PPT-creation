# One-Click PPT

Turn a bare topic into a complete business deck — outline, slide text, and speaker notes — with one prompt.

## What it does

One-Click PPT is a small Agent Skill that turns a topic into a presentation-ready deck: a structured outline, per-slide headlines, bullets, visual suggestions, and speaker notes. It works in clients that support the Agent Skills format, including Claude Code, Cursor, Codex, and Gemini CLI.

No API keys are required. The repository contains a `SKILL.md` file, supporting reference docs, and six optional helper scripts: `tools/deck_lint.py` cross-checks a multi-artifact deck pack, `tools/deck_review.py` audits a deck that already exists, `tools/deck_qa.py` checks whether the slides will work in a room, `tools/render_pptx.py` renders a payload into a real `.pptx`, `tools/theme_apply.py` restyles a `.pptx` to a bundled theme, and `tools/source_extract.py` condenses attached source material into one `source-brief.json`. Only the renderer and the theme tool need `python-pptx`; the rest are standard library only. PDF, Word, PowerPoint and Excel inputs to the extractor need `pypdf`, `python-docx`, `python-pptx` or `openpyxl`.

It produces a slide-by-slide script. By default it does not create a `.pptx` file; the optional renderer turns the structured payload into one, with optional corporate slide-master mapping.

## Why

Most agents produce either a flat bullet dump or a half-baked outline when asked for slides. This skill bakes in the structure that makes business decks actually work: one message per slide, claim-style headlines, metrics-first copy, and notes the presenter can actually speak.

## Install and compatibility

Copy this repository into the skills directory used by your client:

- Claude Code: ~/.claude/skills/
- Cursor: .cursor/skills/
- Codex: .codex/skills/
- Gemini CLI: ~/.gemini/skills/

The exact installation flow can vary by client. Confirm the current skills documentation for the client you use, then open `SKILL.md` as the entry point.

## Usage

Once installed, start with a request such as:

> Create a 10-slide pitch deck for a B2B expense-tracking SaaS. Audience: startup CFOs.

The skill responds with a full slide-by-slide script you can paste into PowerPoint, Keynote, or Google Slides.

## Example output

Prompt: Create a 10-slide pitch deck for a B2B expense-tracking SaaS. Audience: startup CFOs.

```text
# B2B Expense-Tracking SaaS - Pitch Deck (10 slides, ~10 min)

## Slide 1 - Finance teams lose 6 hours a week to manual expense reports
- 68% of expense reports are still processed by hand
- Average cost to process one report: $26
- The problem gets worse as headcount grows
Visual: bar chart of hours lost vs. company size
Notes: "Start with the number that hurts: six hours a week per finance team member. That's the cost of doing expenses by hand, and it scales with every new hire."

## Slide 2 - Manual expense management hides cash flow blind spots
- Reimbursement cycles average 12 days
- 31% of submitted expenses contain errors
- Approvers can't see real-time spend
Visual: timeline of a typical reimbursement cycle
Notes: "Expense data arrives weeks late, so the numbers in the monthly report are already stale. This is the gap we close."

## Slide 3 - SpendBoard automates the entire expense lifecycle
- Receipts captured from email and photos, auto-categorized
- Policy checks run before submission, not after
- Approvals happen in Slack, reimbursements in two clicks
Visual: product screenshot of an auto-categorized receipt
Notes: "Every step that used to take a human now runs automatically. The employee sends a receipt, the policy check happens instantly, and the CFO sees spend in real time."

## Slide 4 - Setup takes one afternoon, not one quarter
- Native integrations with QuickBooks, Xero, and NetSuite
- No custom workflows to build -- templates for 40+ policies
- Employees adopt it in days, not months
Visual: row of integration logos
Notes: "We've seen teams go live in a single afternoon. The hard part of deployment is usually policy configuration, and that's already done for you."

## Slide 5 - The market is large and still moving to software
- $61B spent on business travel and expense annually in the US
- Cloud expense tools growing 18% YoY
- Only 35% of mid-market companies use a dedicated tool
Visual: market size chart with growth trend
Notes: "The category is real and growing, but most mid-market companies still run expenses on spreadsheets. That's the whitespace we're going after."

## Slide 6 - Competitors force a choice: flexible or controlled
- Legacy suites are rigid and slow to configure
- Consumer apps lack policy enforcement
- SpendBoard gives CFOs control without killing flexibility
Visual: 2x2 positioning matrix
Notes: "Incumbents make you choose between control and usability. We built SpendBoard to deliver both, which is why it fits mid-market so well."

## Slide 7 - Traction: 240 companies, 92% net revenue retention
- 240 paying customers, up from 140 a year ago
- 92% net revenue retention, 4.1/5 G2 rating
- Average customer saves $38K/year in processing costs
Visual: growth chart of paying customers
Notes: "The retention number is the one to hold onto: customers who stay keep expanding. Growth is compounding, not linear."

## Slide 8 - We charge per active user, no setup fees
- $9/user/month, annual plans get two months free
- Enterprise tier adds SSO, audit logs, and a custom policy engine
- 30-day pilot with dedicated onboarding help
Visual: pricing table
Notes: "Pricing is simple and predictable. The pilot is free for 30 days, fully supported, so the only risk is the time it takes to try it."

## Slide 9 - The team has shipped fintech at scale
- Founders built payments infrastructure at two unicorns
- 18 engineers, 3 of them former finance ops leads
- Advisory board includes two former Fortune 500 CFOs
Visual: team photos with one-line bios
Notes: "We've built this exact category of software before, and we've lived in the finance ops seat too. That combination is rare in this space."

## Slide 10 - We're raising $6M to double down on mid-market
- Funding extends runway to 24 months
- Hiring 12 in sales and 6 in engineering
- First check closes this quarter; we'd love you to lead it
Visual: "The ask" slide with clear numbers
Notes: "Here's what we need: $6M to scale sales and engineering. We're closing the round this quarter and would love to have you on the cap table."
```

## Structure

```text
repository-root/
├── SKILL.md                       # main instructions
├── README.md
├── CHANGELOG.md
├── ROADMAP.md
├── CONTRIBUTING.md
├── SECURITY.md
├── assets/
│   ├── layouts.json               # 14 slide roles, 31 variants, copy budgets
│   └── themes/
│       ├── consulting.json        # navy + blue accent
│       ├── swiss.json             # black on white, one red accent
│       └── editorial.json         # warm paper, serif headlines
├── references/
│   ├── slide-structures.md        # 21 deck structures by purpose
│   ├── copywriting-guide.md       # copy rules and examples
│   ├── design-guide.md            # layout, type scale, colour, charts
│   ├── zh-cn-adaptation.md        # Chinese-language adaptation
│   ├── output-contract.md         # optional JSON/YAML deck payload
│   ├── export-checklist.md        # pre-export hard/soft gates
│   ├── html-export.md             # single-file HTML deck convention
│   ├── rendering-handoff.md       # payload → .pptx render workflow and naming
│   ├── master-mapping.md          # corporate slide-master layout/placeholder mapping
│   ├── deck-review.md             # deck audit: hard gates, finding codes, scoring
│   ├── source-brief.md            # source brief: sections, chunks, tables, numbers, evidence
│   ├── layout-library.md          # the 14 slide roles, bands and copy budgets
│   ├── themes.md                  # the three themes, contrast floors, adding a theme
│   ├── visual-qa.md               # QA101-QA114, scoring, reading a report
│   └── rehearsal-notes.md · executive-one-pager.md · audience-simulation.md    # speaker-only notes pack; pre-delivery seat pass
├── tools/
│   ├── deck_lint.py               # pack consistency checker (optional)
│   ├── deck_review.py             # existing-deck auditor (optional)
│   ├── render_pptx.py             # payload → .pptx renderer (optional, needs python-pptx)
│   ├── theme_apply.py             # re-skin a .pptx to a bundled theme (optional, needs python-pptx)
│   ├── deck_qa.py                 # will these slides work in a room (optional)
│   └── source_extract.py          # source documents → one source-brief.json (optional)
└── examples/
    ├── status-report.md
    ├── status-report.json         # same deck as structured payload
    ├── status-report.html         # same deck as offline HTML
    ├── status-report-notes.md     # same deck as rehearsal talk track
    ├── deck-review.example.md     # worked review of status-report.md
    ├── audience-simulation.example.md   # worked seat-by-seat pass on the same deck
    ├── master-map.example.json    # worked corporate master map
    ├── crisis-comms.md            # crisis communication — platform outage
    ├── investor-update.md
    └── training.md
```

## Reference files

| File | Load it when |
|------|--------------|
| `references/slide-structures.md` | Choosing a deck structure |
| `references/copywriting-guide.md` | Writing or fixing slide copy |
| `references/design-guide.md` | Building the deck into slides |
| `references/zh-cn-adaptation.md` | The deck is in Chinese |
| `references/output-contract.md` | The user wants JSON/YAML or a rendering payload |
| `references/export-checklist.md` | Before any hand-off or render |
| `references/html-export.md` | The user wants a single-file HTML deck |
| `references/rendering-handoff.md` | The user wants a real `.pptx` file (incl. chart / table layers) |
| `references/master-mapping.md` | The deck must land in a corporate slide master |
| `references/deck-review.md` | Auditing a deck that already exists |
| `references/audience-simulation.md` | Stress-testing the deck against the room before a decision meeting |
| `references/rehearsal-notes.md` | The user wants a rehearsal / speaker-only script |
| `references/layout-library.md` | Choosing a layout, or sizing copy to a band |
| `references/themes.md` | Re-skinning a deck, or adding a theme |
| `references/visual-qa.md` | Checking a deck before it leaves, or reading a QA report |

## Examples

| Example | Structure |
|---------|-----------|
| [status-report.md](examples/status-report.md) | Status report — Q3 platform migration |
| [status-report.json](examples/status-report.json) | Same deck as a structured JSON payload |
| [status-report.html](examples/status-report.html) | Same deck as an offline HTML presentation |
| [status-report-notes.md](examples/status-report-notes.md) | Same deck as a rehearsal talk track |
| [deck-review.example.md](examples/deck-review.example.md) | Worked review report for the status-report deck |
| [audience-simulation.example.md](examples/audience-simulation.example.md) | Worked three-seat simulation of the same deck |
| [master-map.example.json](examples/master-map.example.json) | Worked corporate master map (layouts + placeholders) |
| [qa-report.example.md](examples/qa-report.example.md) | Worked visual QA report (80/100) for the status-report deck |
| [data-layer.example.json](examples/data-layer.example.json) | Same status deck with native charts and a table (schema 1.1) |
| [crisis-comms.md](examples/crisis-comms.md) | Crisis communication — platform outage |
| [investor-update.md](examples/investor-update.md) | Investor update — seed stage |
| [training.md](examples/training.md) | Training — expense policy |

## Validate a deck pack (optional)

When the same deck ships as more than one artifact — Markdown plus a JSON payload, a rehearsal notes pack, an offline HTML file — the copies drift as soon as one of them is edited alone. `tools/deck_lint.py` reads the pack and cross-checks the copies against the JSON payload and `references/output-contract.md`:

```bash
python tools/deck_lint.py examples/status-report
python tools/deck_lint.py examples/status-report --strict   # warnings fail too
```

It checks slide counts, headline wording, timing math, per-slide note budgets and the numeric claims each copy repeats, then reports hard-gate errors and soft warnings. The exit code is 1 on failure, so it drops straight into CI. Standard library only, no install step.

## Review an existing deck (optional)

When the deck already exists — a colleague's draft, last quarter's deck, or one you have just written — audit it before rewriting anything:

```bash
python tools/deck_review.py examples/status-report.md
python tools/deck_review.py examples/status-report.json --json
python tools/deck_review.py examples/status-report.md --slot 5 --out review.md
```

`tools/deck_review.py` reads a Markdown deck or an output-contract payload and reports the hard gates that block a hand-off, the warnings worth a look, a 0-100 score across structure, copy, evidence and delivery, and a READY / REVISE / REWRITE verdict. Add `--slot <minutes>` to check the deck against a time slot, `--min-score <n>` to fail under a score, and `--strict` to fail on warnings as well; the exit code is 0 only when the run passes, so it drops straight into CI. Chinese decks are reviewed in characters per minute, matching `references/zh-cn-adaptation.md`. Standard library only, no install step. Every check and finding code is documented in `references/deck-review.md`, and `examples/deck-review.example.md` is a worked report on the status-report deck.

The review is static, so pair it with the seat-by-seat pass in `references/audience-simulation.md` before a decision meeting: pick two or three seats (exec sponsor, sceptic, operator), ask each seat's questions against the slides, mark every answer answered / partial / gap, then add only what the gaps require. `examples/audience-simulation.example.md` works through the same deck.

## Render to .pptx (optional)

The skill's default output is the slide script. When the user wants an actual file, the structured payload from `references/output-contract.md` is enough: `tools/render_pptx.py` writes one slide per payload slide and carries the speaker notes into the PowerPoint notes pane. A slide may also carry a `chart` or `table` block, which becomes a native, editable PowerPoint object laid out beside the copy — no images, no re-typing the data.

```bash
pip install python-pptx
python tools/render_pptx.py examples/status-report.json                    # bundled Office master
python tools/render_pptx.py examples/data-layer.example.json               # charts + table as native objects
python tools/render_pptx.py deck.json --check                              # resolve layouts, write nothing
python tools/render_pptx.py deck.json --template acme.potx \
    --master-map acme-master-map.json                                      # corporate master
```

Output follows the export naming convention: `{deck-slug}_{version}_{YYYYMMDD}.pptx`, or `{deck-slug}_{version}_{slot}min_{YYYYMMDD}.pptx` with `--slot`. Layout and placeholder resolution is described in `references/master-mapping.md` (name → keyword → index, with per-role placeholder indices); the full workflow, dependency and troubleshooting notes are in `references/rendering-handoff.md`. `python-pptx` is the only third-party dependency in the repository (the renderer and the theme tool use it) — if it cannot be installed, hand over the Markdown deck plus the payload instead.

## Check the slides before they leave (optional)

Rendering proves the file exists; it does not prove the slides work in a room. `tools/deck_qa.py` reads a payload, the copy budgets in `assets/layouts.json` and — optionally — a theme, then reports what a reader would notice:

```bash
python tools/deck_qa.py examples/status-report.json                      # 80/100 (B), four warnings
python tools/deck_qa.py deck.json --theme swiss                          # also checks contrast
python tools/deck_qa.py deck.json --strict --report qa.md                # CI gate plus Markdown report
python tools/deck_qa.py deck.json --json                                 # machine-readable
```

Fourteen rules cover headline length and honesty, bullet count and length, unsupported figures, notes pace, chart and table load, repeated openers and unreadable palettes (QA101-QA114, all documented in `references/visual-qa.md`). Errors mean the slide cannot do its job; warnings mean the room will feel it; notes are opportunities and never cost a point. The score starts at 100 and loses 15 per error and 5 per warning. `examples/qa-report.example.md` is a worked report on the status-report deck: a label headline, a 15-word bullet, three slides carrying figures with no chart.

It is standard library only, and it deliberately does not gate density the user asked for — a data appendix is allowed to break the word budget; say so in the hand-off instead of trimming it.

## Theme a deck (optional)

`tools/theme_apply.py` re-skins an existing `.pptx` to one of three bundled themes: backgrounds, title and body type, chart series colours, table header fills and cell type. Geometry is untouched, so it works on a deck a designer has already laid out, and it can be re-run when the brand moves.

```bash
python tools/theme_apply.py deck.pptx --list                             # consulting, swiss, editorial
python tools/theme_apply.py deck.pptx --theme swiss
python tools/theme_apply.py deck.pptx --theme editorial --out board_q3.pptx
python tools/theme_apply.py deck.pptx --theme swiss --check              # validate contrast only
```

| Theme | Reads as | Use it for |
|-------|----------|------------|
| `consulting` | Navy ink, blue accent, generous side margin | Client work, board packs, anything reviewed by a partner |
| `swiss` | Black on white, one red accent, tight grid | Design reviews, product launches, a room that distrusts decoration |
| `editorial` | Warm paper, serif type, brick accent | Narrative decks, investor updates, anything read as well as watched |

A theme is rejected when text cannot be read from the back of a room: `ink` on `bg` must clear 7:1, `muted` 4.5:1, `accent` 3:1, and no type below 9pt. `--check` and `tools/deck_qa.py --theme` both enforce those floors. Theme anatomy, the contrast table and how to add your own palette: `references/themes.md`.

## Related projects

- [mavplan](https://github.com/TianHengZhuang/mavplan) — UAV mission planning & training CLI
- [mavplan-web](https://github.com/TianHengZhuang/mavplan-web) — browser console for mavplan
- [Chinese-WebNovel-Master](https://github.com/TianHengZhuang/Chinese-WebNovel-Master) — Chinese web-fiction agent workflow

## License

MIT