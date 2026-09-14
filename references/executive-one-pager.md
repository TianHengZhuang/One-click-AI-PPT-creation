# Executive One-Pager

Turn a finished deck into a single-page executive brief for readers who will never sit through the talk.

## When to use

- User asks for a "one-pager", "executive summary", "leave-behind", or "email version"
- After the slide deck is stable (do not draft the one-pager before the story is)
- Optional Step 6 in SKILL.md when the audience includes sponsors who skim

## Page budget

- **300–450 Chinese characters** or **180–280 English words** of body copy
- Plus: title, 3–5 key numbers, one ask, owner + date
- One screen when pasted into email; prints on A4 with 2 cm margins

## Required blocks

| Block | Content | Max |
|-------|---------|-----|
| Title | Same claim as deck title / slide 1 headline | 1 line |
| Situation | Why this matters now (1–2 sentences) | 40 words |
| Key numbers | 3–5 metrics lifted from the deck (same figures!) | list |
| Recommendation | The decision or action you want | 1 sentence |
| Risks / trade-offs | Honest top 2, with mitigations | 2 bullets |
| Next steps | Owner · date · first checkpoint | 1 line |

## Rules

1. **No new facts.** Every number must appear in the deck. If the one-pager needs a fact, fix the deck first (and re-run `tools/deck_lint.py` when a pack exists).
2. **Claim headlines only.** The title must be a takeaway, not a topic label.
3. **One ask.** If you need two decisions, you have two one-pagers or a longer deck.
4. **Skimmable.** Prefer short paragraphs and a metrics row over dense prose.
5. **Language.** Match the deck language; do not mix zh/en mid-page unless the org is bilingual.

## Template

```markdown
# <Claim title>

**Situation**  
<1–2 sentences: context and trigger>

**Key numbers**
- <metric> — <why it matters>
- <metric> — <why it matters>
- <metric> — <why it matters>

**Recommendation**  
<One sentence decision or action>

**Risks**
- <risk> → <mitigation>
- <risk> → <mitigation>

**Next steps**  
<Owner> · <date> · <first checkpoint>
```

## Quality gate

Before hand-off, check:

- [ ] Title is a claim, not a label  
- [ ] All numbers match the deck exactly  
- [ ] Exactly one recommendation/ask  
- [ ] Fits one page without shrinking below 11pt  
- [ ] No bullet longer than two lines  
