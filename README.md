# One-Click PPT

Turn a bare topic into a complete business deck — outline, slide text, and speaker notes — with one prompt.

## What it does

One-Click PPT is a small Agent Skill that turns a topic into a presentation-ready deck: a structured outline, per-slide headlines, bullets, visual suggestions, and speaker notes. It works in clients that support the Agent Skills format, including Claude Code, Cursor, Codex, and Gemini CLI.

No API keys or dependencies are required. The repository contains a `SKILL.md` file, supporting reference docs, and one optional helper script — `tools/deck_lint.py` — that cross-checks a multi-artifact deck pack.

It produces a slide-by-slide script; it does not create a `.pptx` file.

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
├── references/
│   ├── slide-structures.md        # 16 deck structures by purpose
│   ├── copywriting-guide.md       # copy rules and examples
│   ├── design-guide.md            # layout, type scale, colour, charts
│   ├── zh-cn-adaptation.md        # Chinese-language adaptation
│   ├── output-contract.md         # optional JSON/YAML deck payload
│   ├── export-checklist.md        # pre-export hard/soft gates
│   ├── html-export.md             # single-file HTML deck convention
│   └── rehearsal-notes.md · executive-one-pager.md         # speaker-only notes pack
├── tools/
│   └── deck_lint.py               # pack consistency checker (optional)
└── examples/
    ├── status-report.md
    ├── status-report.json         # same deck as structured payload
    ├── status-report.html         # same deck as offline HTML
    ├── status-report-notes.md     # same deck as rehearsal talk track
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
| `references/rehearsal-notes.md` | The user wants a rehearsal / speaker-only script |

## Examples

| Example | Structure |
|---------|-----------|
| [status-report.md](examples/status-report.md) | Status report — Q3 platform migration |
| [status-report.json](examples/status-report.json) | Same deck as a structured JSON payload |
| [status-report.html](examples/status-report.html) | Same deck as an offline HTML presentation |
| [status-report-notes.md](examples/status-report-notes.md) | Same deck as a rehearsal talk track |
| [investor-update.md](examples/investor-update.md) | Investor update — seed stage |
| [training.md](examples/training.md) | Training — expense policy |

## Validate a deck pack (optional)

When the same deck ships as more than one artifact — Markdown plus a JSON payload, a rehearsal notes pack, an offline HTML file — the copies drift as soon as one of them is edited alone. `tools/deck_lint.py` reads the pack and cross-checks the copies against the JSON payload and `references/output-contract.md`:

```bash
python tools/deck_lint.py examples/status-report
python tools/deck_lint.py examples/status-report --strict   # warnings fail too
```

It checks slide counts, headline wording, timing math, per-slide note budgets and the numeric claims each copy repeats, then reports hard-gate errors and soft warnings. The exit code is 1 on failure, so it drops straight into CI. Standard library only, no install step.

## Related projects

- [mavplan](https://github.com/TianHengZhuang/mavplan) — UAV mission planning & training CLI
- [mavplan-web](https://github.com/TianHengZhuang/mavplan-web) — browser console for mavplan
- [Chinese-WebNovel-Master](https://github.com/TianHengZhuang/Chinese-WebNovel-Master) — Chinese web-fiction agent workflow

## License

MIT