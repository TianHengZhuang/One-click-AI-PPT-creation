# Audience simulation

Stress-test a deck against the room before the room gets to it.

`deck_review` checks the deck against the rules. Audience simulation checks it against people: what each seat will ask, which slide answers it, and where the deck goes silent. It is the difference between a deck that is well built and a deck that survives the meeting.

## When to use it

- Before a meeting where someone can say no: a decision review, a budget ask, a hostile design review, a board or investor readout, a competitive pitch.
- Before any presentation where you have been asked to "pre-read" instead of present - the deck has to answer questions nobody is in the room to clarify.
- Not for routine status updates to a friendly audience, unless the number is bad news.

## Pick two or three seats

A seat is a perspective with something at stake, not a personality. Pick the ones who can change the outcome.

| Deck type | Seats to simulate |
|-----------|-------------------|
| Internal status / decision | decision-maker, skeptic (a peer whose work the deck affects), affected (the person who runs it afterwards) |
| Proposal / business case | buyer, budget holder, technical evaluator |
| Customer pitch | champion, technical blocker, procurement |
| Post-mortem / incident review | the executive who reads the recap, the engineer who owns the fix, the customer-facing lead |

Three seats maximum. More dilutes the simulation into a list of generic questions. Never simulate your own seat - you already know your answers.

## Procedure

1. **State the seats.** One line each: what they control, and the objection they arrive with.
2. **Ask their questions against the deck.** Every question carries an anchor: slide number and bullet. Ask the question the seat would actually ask, in their voice and with their priorities - the budget holder asks what it costs, the operator asks who is on call.
3. **Mark each question.** `answered` (the deck or its notes carry it), `partial` (the deck implies it but does not say it), `gap` (the deck has nothing).
4. **Judge the room.** Say whether the deck gets the decision it asks for. If the ask is on the last slide, the simulation must say whether the room can grant it with what the slides show.
5. **Recommend the smallest fix set.** Two to four changes. Each one is additive - a number, an owner, a date, a name - not a rewrite. The message belongs to the author.

## Rules

- **Anchor everything.** A question with no slide reference is the simulator's opinion, not a finding.
- **Write down only what the deck says.** No outside knowledge, no "they probably know this from the thread". If the number is not on the slide or in the notes, the answer is a gap, even when you know the number.
- **Ask the likely objection, not the clever one.** Simulate the question that will actually be asked first, not the most interesting hypothetical.
- **The notes count.** A figure in the speaker notes is available to the presenter; a figure in nobody's head is not.
- **Report, do not repair.** The simulator's product is a gap list. Fixing is a separate pass, and the writer owns the wording.
- **One page per seat.** A simulation is a stress test, not a script.

## Output

```markdown
## Seat: <name>

| # | Question | Anchor | Status |
|---|----------|--------|--------|
| 1 | ... | Slide 4, bullet 2 | gap |

## Verdict
Does the deck survive the room? Which question gets silence?

## Recommended deck changes

| Change | Slide | Why |
|--------|-------|-----|
| ... | ... | ... |
```

Severity, so the author knows what to do first:

| Severity | Meaning |
|----------|---------|
| blocking | The decision cannot be made without it |
| worth fixing | The deck looks thin, but the meeting still works |
| cosmetic | The author may ignore it |

## Common failure modes

- **Straw man.** "The audience might not understand the domain." That is not a question a seat asks. Ask what the seat asks, with their priorities.
- **Invented facts.** Do not answer "what does the fallback cost?" with a number the deck never states. The finding is that the number is missing - that is the gap.
- **Credit for invisible work.** The author researched it, so the answer feels present. If it is not on the slide, the seat cannot see it.
- **Simulation as rewrite.** Producing a new deck defeats the purpose: the author needs to know where the holes are, not to receive a different deck.
- **Friendly seats only.** If every seat is sympathetic, the simulation will report that the deck is fine. Include the one who benefits from saying no.

## Pairing with the rest of the flow

```text
write the deck  ->  tools/deck_review.py    (rules: gates, score, verdict)
                ->  audience-simulation.md  (people: questions, gaps, fixes)
                ->  references/export-checklist.md (hand-off gates)
```

Worked example: `examples/audience-simulation.example.md`.
