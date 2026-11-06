---
name: shift-start
description: Takes over work from a shift-change handover. Lists the handovers waiting in .shift/ so the user only confirms a session name, reads the files the handover marks as required reading, checks it against the real world (git state, files, running jobs), reads back its understanding and top uncertainties, waits for the user to confirm before acting, then deletes the handover it consumed. Use at the start of a session when the user says "shift start", "pick up where we left off", "continue from the handover", "resume the last session", or when a handover exists in .shift/ and the user asks to continue earlier work.
---

# shift-start

This is the receiving half of an I-PASS handoff: the incoming person reads the handoff back **before** touching anything. That readback is where misunderstandings get caught cheaply, while one sentence from the user can still fix them.

## 1. Find the handover and confirm which session it is

List the handovers in `.shift/` (each file is named `<session-name>-<date>-<time>.md`; `LATEST.md` is only a copy of the newest one). Then:

- The user named a session, or there is exactly one: use it, and open your reply by naming it, e.g. "Picking up **clip-sweep** (written yesterday 19:47)."
- Several are waiting: list them as name + when written + the one-line goal from each file, and ask which one. A name is all you need; don't make the user type a path.
- None exist: say so and suggest running `/shift-change` at the end of the previous session.

Mention any handover older than about two weeks as possibly stale, and read the chosen one in full.

Read the whole thing. Treat the **taste table** ("Working with …") as rules for how to work with this user, not as background. Treat the **no-go zones** as closed unless their reopen condition is met.

## 2. Read the required files before you say anything about the work

The handover lists files under "Read these first". **Read every one of them now**, in full, before the readback. These are the standards, protocols and specs the user and the previous session agreed on; the handover deliberately points at them instead of summarising them, so skipping them means working to rules you have not seen. This is the step most likely to be skipped and the one that causes "the new session doesn't get it".

If a required file is missing or has changed since the handover was written (check `git log -1 -- <path>`), say so in the readback rather than guessing. If the handover lists no required reading but the repo has obvious standards files (`CLAUDE.md`, `AGENTS.md`, a protocol or spec under `docs/`), read those and say you did.

## 3. Check the handover against the world

The handover describes the world when it was written. Check what has changed since, without fixing anything yet:

- git branch, HEAD, and uncommitted changes versus what the handover says.
- Files in the file map and experiment outputs: do they exist?
- Running jobs: are they still running, finished, or dead? Look at the job IDs and log files listed.
- Anything tagged `[assumed]` that you can confirm cheaply (one command, one file read).

## 4. Read back

Reply in the user's language, in this shape and briefly: this is a check, not a report.

- **Where we are**: one sentence.
- **Read**: each required file, one line each on the rule you took from it (this is how the user sees you actually read them, not that you skimmed the handover).
- **What I'll do next**: the first action and how I'll know it's done.
- **Rules I'll follow**: the top 3 from the taste table, in my own words.
- **What I won't do**: the no-go zones that matter for the next action.
- **World check**: what matches, what has drifted (e.g. "job 481516 finished, and the results are in runs/sweep3/").
- **Least sure about**: up to 3 specific questions whose answers would change what I do.

## 5. Wait

Stop and wait for the user to confirm or correct you. Starting on a misread handover costs far more than one round-trip. When they correct something, that correction is new taste: keep it in mind so the next `/shift-change` records it.

## Gotchas

- **Skipping the required reading is the main failure mode.** The handover points at standards instead of quoting them, so if you don't open them you are working to rules you have never seen, while feeling informed.
- **The world moved on.** Branches changed, jobs finished or died, files were edited by the user between sessions. Check before you trust any state in the document.
- **A handover can be wrong.** It was written by an agent under time pressure. Treat `[assumed]` as unverified, and say when the repository contradicts the document rather than making the two agree silently.
- **Don't act during the readback.** The point is to be corrected before any work happens; running the first action early throws that away.
- **Don't delete anything the user hasn't consumed.** Only the handover you actually picked up, and only after they confirm.

## 6. Once confirmed, clear the handover away

A handover exists to be consumed. After the user confirms your readback, delete the file you picked up and, if `.shift/LATEST.md` is a copy of it, delete that too, then say in one line which file you removed. `.shift/` should only ever hold sessions still waiting to be picked up, so nobody has to guess which of five documents is current.

Two things survive the deletion, so nothing important is lost:
- Everything you need for the work is now in your context, and the next `/shift-change` will write a fresh handover.
- Durable preferences belong in `CLAUDE.md`, not in a handover; if the handover lists some that are not there yet, offer to add them before deleting.

Keep the file if the user says so, if they haven't confirmed your readback, or if they are only browsing ("what's in the handover?") rather than picking the work up.
