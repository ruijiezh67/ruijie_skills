---
name: shift-recover
description: Rebuilds the state of a session that ended without a handover, after a usage limit, a crash, a closed laptop or a forgotten /clear. Lists the recent sessions for this directory so the user confirms which one, mines its transcript for the last plan, the corrections and what was in flight, checks what actually finished (git state, background and cluster jobs, half-written outputs), then reads back a resume plan and waits before acting. Use when the user says "we hit the limit", "the session died", "continue from yesterday", "I forgot to hand over", "what was I doing", "recover the last session", or when work clearly continues from an earlier session and no handover exists in .shift/.
compatibility: scripts in the shift-change skill need Python 3.8+ (standard library only) and read Claude Code transcripts; without them this skill still works from the repository state alone.
---

# shift-recover

A planned handover is cheap; an unplanned stop is what actually happens. The usage limit hits, the laptop closes, a run eats the context, someone types `/clear`. There is no handover, and the next session starts from nothing while half-finished work sits in the repo and jobs may still be running.

This skill reconstructs that state from what survived: the transcript on disk, the repository, and the machines.

## 1. Pick the session, by name not by id

Run `python "${CLAUDE_SKILL_DIR}/../shift-change/scripts/mine_transcript.py" --list` (or the same script inside the shift-change skill directory) to list recent sessions for this directory: id, time span, number of prompts, opening line. Show the user that list in a readable form and let them confirm with a word ("yesterday's", "the sweep one"). If only one plausible session exists, name it and continue.

If no transcript survives (Claude Code deletes old sessions, around 30 days by default), say so plainly and rebuild from the repository alone; everything below except step 2 still applies.

## 2. Mine the transcript

Run the same script with `--session <id>`. It prints the user's messages (corrections flagged, pre-compaction ones labelled), rejected tool calls and interruptions, files edited and read, and the commands that may still be running. Read it for four things:

- **The last intent**: what the user asked for most recently, and what the agent was in the middle of doing.
- **Corrections and preferences**, in the user's own words.
- **In-flight work**: background commands, cluster submissions, long-running scripts.
- **The stopping reason**: a usage-limit message, an interrupt, a crash, or simply the end. If the limit was hit, note the reset time it printed; that is when the work can continue.

## 3. Check what actually happened while nobody was watching

The transcript says what was *started*. Only the machine says what *finished*:

- `git status`, `git diff --stat`, `git log --oneline -10`: committed, uncommitted, or never saved.
- Outputs the session was producing: do the files exist, are they complete, are they truncated or zero-length?
- Background and cluster jobs: still running, finished, or dead (`squeue -u $USER`, `tmux ls`, the job's log file, the process list). A job that was launched is not a job that succeeded.
- Partial state that will break a rerun: lock files, half-written caches, a results directory with a few files in it.

Distinguish three cases for each piece of work and say which it is: **done**, **partly done** (name exactly what exists), **not started**.

## 4. Read back a resume plan, then wait

Reply briefly, in the user's language:

- **Where it stopped**: one sentence, including why (limit, interrupt, crash, unknown).
- **What survived**: done / partly done / not started, with the evidence for each.
- **What is still running**, if anything, and when to look.
- **Rules I picked up**: the corrections and preferences from the transcript, in the user's words.
- **What I'd do first**, and how I'll know it worked. Where work was partly done, say whether to resume it or redo it, and why.
- **Least sure about**: up to 3 questions whose answers change the plan.

Then stop and wait for confirmation. After an unplanned stop the repository is often in a state nobody intended, so acting before the user confirms is how half-finished work gets overwritten.

## 5. Write the handover that was never written

Once the user confirms, run the `shift-change` skill to save this reconstructed state as a proper handover, so the next interruption costs nothing. If the usage limit is still in force, write it in `quick` mode: no exam, no subagents.

## Gotchas

- **Transcripts expire.** Around 30 days by default. Recovery gets weaker with time, which is an argument for a handover, not against recovery.
- **"It was running" is not "it ran".** Check the log, the exit status, the output file; a usage limit or a closed laptop kills children too.
- **A usage limit stops the agent, not the cluster.** Jobs submitted before the stop may have finished hours ago; results may be waiting.
- **Don't rerun blindly.** A partly written output directory can make a rerun look successful while mixing old and new results. Say what exists before proposing a rerun.
- **The last message may be the agent's own plan, not the user's.** Separate what the user asked for from what the agent decided to do next.
- **Uncommitted work is the most fragile thing in the repo.** Mention it early, and offer to commit or stash it before anything else touches the tree.

## When not to use this

- A handover exists in `.shift/`: use `shift-start`, which is cheaper and more accurate.
- The session is still alive and you simply want to continue: just continue.
- The user wants to end a session in an orderly way: that is `shift-change`.
