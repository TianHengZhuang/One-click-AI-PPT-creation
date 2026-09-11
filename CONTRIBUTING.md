# Contributing

Thanks for considering a contribution to One-Click AI PPT.

## What this repository is

An Agent Skill. `SKILL.md` holds the instructions; everything else is reference material the skill loads on demand.

## Ways to contribute

- Report a structure that produces weak decks
- Propose a new deck structure
- Improve a copywriting example
- Add a worked example deck
- Fix typos and unclear instructions

## Ground rules

- Instructions must be executable by an agent without extra interpretation.
- Every rule needs an example or a clear failure case.
- No scripts, API keys or network calls. The skill must run with plain file reads.
- Keep the skill client-agnostic: Claude Code, Cursor, Codex, Gemini CLI.

## Writing style

- Short sentences. One instruction per line.
- Imperative mood: "Lead with the metric", not "The metric should be led with".
- Business English. No marketing adjectives.
- `-` for lists, `##` for sections, backticks for file paths.

## Adding a deck structure

Edit `references/slide-structures.md`:

1. Number it in sequence.
2. State the slide count.
3. Give one line per slide.
4. Add to "Rules of thumb" only if it changes a general rule.

## Adding a reference file

1. Place it in `references/`.
2. Open with one line stating when to load it.
3. Reference it from `SKILL.md`.

## Commit messages

| Prefix | Use |
|--------|-----|
| feat | New structure, reference file or example |
| fix | Correction to an existing rule |
| docs | README, ROADMAP, CHANGELOG |
| chore | Housekeeping |

## Pull requests

One concern per pull request. Describe the deck scenario that motivated the change.

## License

By contributing you agree that your contribution is licensed under the MIT License.
