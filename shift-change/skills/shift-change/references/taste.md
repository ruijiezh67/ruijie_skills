# Taste: what the user corrected, turned into rules

Taste is the part of a session that never shows up in the diff: how much detail the user wants, how bold to be, what words and patterns annoy them, when to ask and when to just act. It is learned by being corrected, so the corrections are the raw material.

## Where corrections hide

Look in the transcript digest and your context for:

- **Negation after your action**: "no", "don't", "stop", "that's not what I meant", "why did you…".
- **Interruptions**: the user stopped you mid-action. What they said next is almost always a correction.
- **Rejected tool calls**, especially with a reason given.
- **The user rewriting your output**: they changed your wording, cut your paragraph, renamed your variable. The diff between your version and theirs is pure taste.
- **Repeated requests**: they asked for the same thing twice. That means you failed the first time, and it matters to them.
- **Explicit preferences**: "I prefer", "always", "from now on", "every time".
- **Praise**: "perfect", "yes, exactly like that". A confirmed choice is taste too, and it is easy to lose because nothing went wrong.

## Write each one as a transferable rule

| I assumed | User corrected | Rule from now on | User's words |
|---|---|---|---|
| a full explanation before the answer | wanted the answer first | lead with the conclusion in ≤ 5 lines; details only on request | "conclusion first" |
| refactor while fixing the bug | only the bug | minimal diffs; propose refactors separately, don't do them | "don't touch what I didn't ask about" |
| run the full test suite after each edit | too slow | run only the affected test file; full suite before commits | "just the one file" |

Rules describe **behaviour you can check**, not adjectives. "Be concise" fails; "≤ 5 lines, no closing recap" works. Keep the user's own words: they carry tone that a paraphrase loses, and the next session can recognise the pattern when it sees it again.

## Task-specific or durable?

Ask: *would this still apply on a different project next month?*

- Durable: communication style, language, autonomy level ("ask before running anything longer than 10 min"), coding style, tools they love or refuse.
- Task-specific: "don't touch `legacy/` in this repo", "the advisor wants Fig. 3 in grayscale".

Both go in the handover. Only durable ones are proposed for long-term memory.

## Saving durable taste

1. Show the user the durable rules as a short list and ask which to keep, and where: this project's `CLAUDE.md` (or `AGENTS.md` for other agents), or the user-level file (e.g. `~/.claude/CLAUDE.md`) for all projects.
2. Read the target file first. Merge into an existing `## Working with me` section (create it if absent); if an existing line says the same thing, sharpen it instead of adding a duplicate; if one contradicts it, ask which wins.
3. Write only what the user approved, in the same rule + words format, one line each.
