# Export readiness checklist

Run this after the deck is written and before handing it to a human or a renderer.

The goal is not perfect design. The goal is that nothing blocks the meeting.

---

## Hard gates

| Check | Pass condition | Fix |
|-------|----------------|-----|
| Slide count | Fits the time slot (see timing model in output-contract.md) | Cut or split slides |
| One message per slide | Headline states the point without the bullets | Rewrite the headline |
| Body size | ≥ 24pt equivalent; ≥ 36pt for headlines | Enlarge or split |
| Contrast | Dark text on light background (or verified high-contrast dark theme) | Swap palette |
| Numbers | Every claim metric has a source note or "internal" label | Add source or soften claim |
| Notes | Each slide has speaker notes under the time budget | Trim notes |
| No orphan charts | Every chart has a title, axis labels, and a one-line takeaway | Label or drop |
| Links | External links are shortened or footnoted; no broken URLs | Fix or remove |

---

## Soft gates (warn, do not block)

- More than 5 bullets on a slide
- Nested bullets
- Full paragraphs instead of fragments
- Two chart types on one slide
- Stock photo with no text overlay story
- jargon the audience would not say out loud

---

## Chart labels

Every chart needs:

1. Title stating the takeaway, not the dataset
2. Axis units
3. Source / period in a footnote
4. One accent color for the highlighted series

---

## Speaker-note budget

Use the timing model from `references/output-contract.md`:

- English ≈ 130 words per minute
- Chinese ≈ 240 characters per minute
- Add 8 seconds per slide for transition

If total notes exceed the slot, cut slides before cutting words to unreadable speed.

---

## Deliverable pack

Before export, name the pack:

```text
<deck-slug>/
  outline.md          # Markdown form
  deck.json           # optional, output-contract
  slides.html         # optional, single-file HTML deck
  notes.md            # optional, notes only for rehearsal
```

Once the pack exists on disk, `python tools/deck_lint.py <deck-path>` re-checks the copies against each other and against `references/output-contract.md`. Hard-gate failures block the hand-off; soft warnings are reported, not enforced.

---

## Output

Emit a short report:

- Hard-gate pass/fail
- Soft-gate warnings
- Recommended export form (Markdown / JSON / HTML)
- Time estimate vs slot
