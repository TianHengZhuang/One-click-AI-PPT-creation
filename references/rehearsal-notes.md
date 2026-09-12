# Rehearsal notes pack

Separate the talk track from the slide body when the speaker needs a rehearsal file.

Do not dump slide bullets into notes. Notes are what you *say*, not what you *show*.

---

## When to emit

- User asks for speaker notes only, a rehearsal file, or a script
- Deck is already written (Markdown and/or JSON)
- Time slot is known or estimated

Pairs with `references/output-contract.md` timing model and `references/export-checklist.md`.

---

## File shape

One Markdown file per deck:

```markdown
# <Deck title> — rehearsal notes

Slot: <N> min · Slides: <M> · Language: <en | zh-CN>

## Slide 1 — <Headline>
**Say (~Xs):**
...

**Watch for:**
- ...

## Slide 2 — <Headline>
...
```

---

## Timing

- English ≈ 130 words per minute
- Chinese ≈ 240 characters per minute
- Add ~8s transition per slide
- Mark each slide with an estimated speaking time

If the pack exceeds the slot, cut slides before speeding up delivery.

---

## Content rules

1. Full sentences you can read aloud once and still sound natural
2. One open question the slide is meant to trigger
3. Numbers spoken the same way they appear on the slide
4. No new facts that are not on the slide or in the backup
5. Optional "Watch for" for likely objections

---

## Relationship to JSON `notes`

If a structured deck already has `notes` per slide, the rehearsal pack expands those into speakable paragraphs. Do not invent a second storyline.

---

## Deliverable pack update

```text
<deck-slug>/
  outline.md
  deck.json
  slides.html
  notes.md          # this file
```
