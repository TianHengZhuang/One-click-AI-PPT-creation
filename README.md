# One-Click AI PPT

Turn a bare topic into a complete business deck — outline, slide text, and speaker notes — with one prompt.

## What it does

One-Click AI PPT is a small Agent Skill that turns a topic into a presentation-ready deck: a structured outline, per-slide headlines, bullets, visual suggestions, and speaker notes. It works in any agent that supports the Agent Skills format — Claude Code, Cursor, Codex, Gemini CLI, and others.

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

## Structure

```
one-click-ai-ppt/
├── SKILL.md                    # main instructions
└── references/
    ├── slide-structures.md     # deck structures by purpose
    └── copywriting-guide.md    # copy rules and examples
```

## License

MIT
