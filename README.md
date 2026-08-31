# One-Click AI PPT

Turn a bare topic into a complete business deck â outline, slide text, and speaker notes â with one prompt.

## What it does

One-Click AI PPT is a small Agent Skill that turns a topic into a presentation-ready deck: a structured outline, per-slide headlines, bullets, visual suggestions, and speaker notes. It works in any agent that supports the Agent Skills format â Claude Code, Cursor, Codex, Gemini CLI, and others.

No API keys, no scripts, no dependencies. Just a `SKILL.md` and a couple of reference docs.

## Why

Most agents produce either a flat bullet dump or a half-baked outline when asked for slides. This skill bakes in the structure that makes business decks actually work: one message per slide, claim-style headlines, metrics-first copy, and notes the presenter can actually speak.

## Install

Copy the `one-click-ai-ppt` folder into your agent's skills directory:

- Claude Code: `~/.claude/skills/`
- Cursor: `.cursor/skills/`
- Codex: `~/.codex/skills/`
- Gemini CLI: `~/.gemini/skills/`

Or clone the repo and symlink it in.

## Usage

Once installed, just ask:

> Create a 10-slide pitch deck for a B2B expense-tracking SaaS. Audience: startup CFOs.

The skill responds with a full slide-by-slide script you can paste straight into PowerPoint, Keynote, or Google Slides.

## Example output

Prompt: `Create a 10-slide pitch deck for a B2B expense-tracking SaaS. Audience: startup CFOs.`

```
# B2B Expense-Tracking SaaS â Pitch Deck (10 slides, ~10 min)

## Slide 1 â Finance teams lose 6 hours a week to manual expense reports
- 68% of expense reports are still processed by hand
- Average cost to process one report: $26
- The problem gets worse as headcount grows
Visual: bar chart of hours lost vs. company size
Notes: "Start with the number that hurts: six hours a week per finance team member. That's the cost of doing expenses by hand, and it scales with every new hire."

## Slide 2 â Manual expense management hides cash flow blind spots
- Reimbursement cycles average 12 days
- 31% of submitted expenses contain errors
- Approvers can't see real-time spend
Visual: timeline of a typical reimbursement cycle
Notes: "Expense data arrives weeks late, so the numbers in the monthly report are already stale. This is the gap we close."

## Slide 3 â SpendBoard automates the entire expense lifecycle
- Receipts captured from email and photos, auto-categorized
- Policy checks run before submission, not after
- Approvals happen in Slack, reimbursements in two clicks
Visual: product screenshot of an auto-categorized receipt
Notes: "Every step that used to take a human now runs automatically. The employee sends a receipt, the policy check happens instantly, and the CFO sees spend in real time."

## Slide 4 â Setup takes one afternoon, not one quarter
- Native integrations with QuickBooks, Xero, and NetSuite
- No custom workflows to build â templates for 40+ policies
- Employees adopt it in days, not months
Visual: row of integration logos
Notes: "We've seen teams go live in a single afternoon. The hard part of deployment is usually policy configuration, and that's already done for you."

## Slide 5 â The market is large and still moving to software
- $61B spent on business travel and expense annually in the US
- Cloud expense tools growing 18% YoY
- Only 35% of mid-market companies use a dedicated tool
Visual: market size chart with growth trend
Notes: "The category is real and growing, but most mid-market companies still run expenses on spreadsheets. That's the whitespace we're going after."

## Slide 6 â Competitors force a choice: flexible or controlled
- Legacy suites are rigid and slow to configure
- Consumer apps lack policy enforcement
- SpendBoard gives CFOs control without killing flexibility
Visual: 2x2 positioning matrix
Notes: "Incumbents make you choose between control and usability. We built SpendBoard to deliver both, which is why it fits mid-market so well."

## Slide 7 â Traction: 240 companies, 92% net revenue retention
- 240 paying customers, up from 140 a year ago
- 92% net revenue retention, 4.1/5 G2 rating
- Average customer saves $38K/year in processing costs
Visual: growth chart of paying customers
Notes: "The retention number is the one to hold onto: customers who stay keep expanding. Growth is compounding, not linear."

## Slide 8 â We charge per active user, no setup fees
- $9/user/month, annual plans get two months free
- Enterprise tier adds SSO, audit logs, and a custom policy engine
- 30-day pilot with dedicated onboarding help
Visual: pricing table
Notes: "Pricing is simple and predictable. The pilot is free for 30 days, fully supported, so the only risk is the time it takes to try it."

## Slide 9 â The team has shipped fintech at scale
- Founders built payments infrastructure at two unicorns
- 18 engineers, 3 of them former finance ops leads
- Advisory board includes two former Fortune 500 CFOs
Visual: team photos with one-line bios
Notes: "We've built this exact category of software before, and we've lived in the finance ops seat too. That combination is rare in this space."

## Slide 10 â We're raising $6M to double down on mid-market
- Funding extends runway to 24 months
- Hiring 12 in sales and 6 in engineering
- First check closes this quarter; we'd love you to lead it
Visual: "The ask" slide with clear numbers
Notes: "Here's what we need: $6M to scale sales and engineering. We're closing the round this quarter and would love to have you on the cap table."
```

## Structure

```
one-click-ai-ppt/
âââ SKILL.md                    # main instructions
âââ references/
    âââ slide-structures.md     # deck structures by purpose
    âââ copywriting-guide.md    # copy rules and examples
```

## License

MIT
