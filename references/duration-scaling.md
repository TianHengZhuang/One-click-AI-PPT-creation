# Duration scaling (3 / 8 / 15 minutes)

Use this when the **same outline family** must work at three common talk lengths.
Do not invent three unrelated decks — scale slide count and notes budget.

---

## Target slots

| Slot | Typical use | Slide budget | Notes budget (CN ≈240 字/分) |
|------|-------------|--------------|------------------------------|
| **3 min** | elevator / standup | 3–5 | ≤ 700 字 total |
| **8 min** | team demo | 6–9 | ≤ 1,900 字 total |
| **15 min** | customer / review | 10–14 | ≤ 3,600 字 total |

Formula reminders (also in `references/output-contract.md`):

- English ≈ 130 wpm
- Chinese ≈ 240 chars / min
- +8 s per slide for transition

---

## Scaling rules

1. **3 min** — keep: one problem, one proof, one ask. Drop appendix structure, secondary metrics, and long backup.
2. **8 min** — keep: problem → evidence → solution → plan. Compress background to one slide.
3. **15 min** — add: deeper data, risks, alternatives considered, next-step timeline.

Always keep **one message per slide**. Scaling cuts *slides*, not headline quality.

---

## Output naming

When exporting three slots from one pack:

```text
{deck-slug}_v{skill}_3min_{YYYYMMDD}.md
{deck-slug}_v{skill}_8min_{YYYYMMDD}.md
{deck-slug}_v{skill}_15min_{YYYYMMDD}.md
```

Or keep JSON twins with `meta.target_minutes` = 3 / 8 / 15 and matching `slide_count` / `est_minutes`.

---

## Lint

Each scaled artifact must still pass `tools/deck_lint.py`:

- `meta.target_minutes` matches the slot
- `sum(est_seconds)/60` within 11% of `meta.est_minutes`
- speaker notes non-empty and within char guidance
- export filename includes the slot
