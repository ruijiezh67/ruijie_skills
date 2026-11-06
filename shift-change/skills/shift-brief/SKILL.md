---
name: shift-brief
description: Packages a local sub-task for a collaborator (usually someone who also works with an AI coding agent) as a self-contained bundle. Traces every file the task needs, sanitizes secrets and absolute paths, writes BRIEF.md and START_HERE.md with acceptance criteria as runnable commands plus a paste-ready prompt for the receiver's agent, then has a fresh agent cold-start from the bundle alone and fixes whatever it got stuck on before anything is sent. Use when the user wants to delegate, hand off or assign part of their work to another person, labmate, student or coauthor, e.g. "hand this to my labmate", "package this task for X", "write a task brief", "delegate this". Not for continuing the user's own work in a new session (use shift-change).
---

# shift-brief

Handing work to another person fails in predictable ways: a file is missing, a path only exists on your laptop, "done" was never defined, and the receiver's agent has none of the context your session built up. This skill produces a bundle that the receiver's agent can pick up in five minutes, and proves it by having a fresh agent try exactly that before anything is sent.

## 1. Pin down the task

State the sub-task back to the user in a few lines: the goal, what is in and out of scope, the deliverable, any deadline, and who receives it. Ask up to 3 questions only where the answer changes the bundle (e.g. "Does the receiver have access to the cluster?", "Chinese, English, or both?"). Everything else you can infer from the session and the repo.

## 2. Trace what the task needs

Follow the task from its entry point outward: the scripts it runs, what they import, the configs and data they load, the files this session read or edited for this part of the work, and the outputs it compares against. Details and heuristics are in `references/bundle.md`. Classify every item:

- **include**: small source files, configs, notes the receiver needs.
- **link**: already reachable (a public repo, a shared drive path, a DOI or URL).
- **regenerate**: derivable outputs; give the exact command instead of the file.
- **manifest only**: large data; list path, size, sha256 and where to get it.

Missing files are the most common failure, so when unsure whether something is needed, list it in the manifest rather than silently dropping it.

## 3. Sanitize

Go through `references/sanitize.md` before writing anything to the bundle: keys and tokens, `.env` files, absolute paths with usernames, private notes, internal hostnames, unpublished data the receiver shouldn't have. Replace rather than delete where it would break something (e.g. `.env` → `.env.example` with placeholders). Keep a list of what you changed; the user sees it in the report.

## 4. Write the bundle

```
<task-slug>-brief/
├── START_HERE.md   the 5-minute path: setup, first command, and a prompt to paste into their agent
├── BRIEF.md        goal, context, what's done, what to do, no-go zones, conventions, acceptance criteria
├── MANIFEST.md     every file: included / link / regenerate / fetch, with sizes and checksums
└── files/          included files at their repo-relative paths
```

Templates are in `references/bundle.md`. Three things make the difference:

- **Acceptance criteria are commands with expected output** ("`python eval.py --split dev` prints `acc >= 0.70`"), not prose like "make sure it works". The receiver's agent can check itself.
- **The no-go zones and conventions travel with the task**: what was tried and rejected (with why), and how the user wants things done (style, tools, what not to touch). These are what a stranger gets wrong.
- **The paste-in prompt** in START_HERE.md tells the receiver's agent to read BRIEF.md, verify the setup, read back its plan to the receiver before starting, and run the acceptance checks at the end.

Write in the language the user chose; for "both", put English and Chinese in the same file, section by section.

## 5. Cold-start test

Copy the bundle to a fresh temporary directory outside the project. Spawn a fresh subagent that sees only that directory and asks it to act as the receiver's agent: follow START_HERE.md, run the setup, confirm every referenced file is present or has a working fetch instruction, and run the acceptance commands. They may fail because the task isn't done yet, but they must *run* and fail for the expected reason. It must not do the task itself. It reports every point where it got stuck, guessed, or needed something not in the bundle.

Fix each gap in the bundle and retest with a new subagent, at most 2 rounds. If no subagent is available, walk through START_HERE.md yourself in the temp copy and say that the test was not independent.

## 6. Deliver

Ask the user how to send it, and see `references/delivery.md`: a zip, a git branch plus a GitHub issue, or a path on a shared server/cluster. Pushing, opening issues, or copying to shared locations is visible to others: confirm with the user before doing it.

## 7. Report

Tell the user: what is in the bundle (counts per class), the cold-start result and what it caught, what was sanitized, where the bundle is, and the one message they can send the receiver.

## Gotchas

- **Missing files are the usual reason a bundle fails.** When unsure whether something is needed, list it in the manifest rather than dropping it.
- **Absolute paths work only on your machine.** `/Users/you/...` and `C:/Users/you/...` in configs or scripts break silently on the receiver's side.
- **Notebook outputs and `.git/` carry history you didn't mean to send.** Strip them before packaging.
- **"Make sure it works" is not an acceptance criterion.** If the check isn't a command with an expected output, the receiver cannot tell when they are done.
- **The acceptance commands should fail at first, for the right reason.** A command that fails because a path is wrong teaches the receiver nothing.
- **Sending is irreversible.** Pushing a branch, opening an issue or copying to a shared drive is visible to others; confirm with the user first.

## When not to use this

- You are continuing your own work later: use `shift-change`.
- The receiver only needs a pointer ("look at issue #12"): just send the pointer.
