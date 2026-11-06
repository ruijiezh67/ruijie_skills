---
name: shift-change
description: Hands the current session over to a fresh one without losing its soul. Writes an I-PASS handover (next actions, mental map, rejected paths with reasons, the user's corrections as rules, required reading, running jobs, gotchas, jargon), mines the raw transcript for corrections that compaction dropped, then quizzes a fresh subagent on the handover and patches the gaps. Use when a long session is ending, context is filling up, before /clear, when switching machines or pausing overnight, and when the user says "shift change", "handover", "hand off to the next session", "wrap up", "save context for later". Prefer it over a plain summary or /compact when the next session must work the way this one did. Not for handing a task to another person (use shift-brief).
compatibility: scripts/mine_transcript.py needs Python 3.8+ (standard library only) and reads Claude Code transcripts; the skill works without it on other agents.
---

# shift-change

When a session ends, the next one usually knows *what* was done but not *how the user wants it done*: which paths were already rejected and why, what the user kept correcting, what is verified versus merely believed, what is still running. It is like an employee leaving and a stranger taking over their desk.

Hospitals solved this with **I-PASS**, a structured shift handoff that cut medical errors by 23% (Starmer et al., NEJM 2014). Its last step is the one everyone else skips: the incoming person **reads the handoff back** so gaps surface before they cause harm. This skill writes an I-PASS handover and then makes a fresh agent read it back as an exam.

Arguments: `quick` skips the exam. Any other text is the goal for the next session.

## Step 1: Gather evidence (don't write from memory alone)

Your context is incomplete: auto-compaction drops early turns, and early turns are where the user corrected you most. Gather from the sources, in this order:

1. **Transcript** (Claude Code only). Run `python "${CLAUDE_SKILL_DIR}/scripts/mine_transcript.py"` from the project root (on agents that don't substitute that variable, use the `scripts/mine_transcript.py` path inside this skill's own directory). It prints every human message (likely corrections flagged ⚑, pre-compaction ones labelled), answers the user gave to questions, rejected tool calls with reasons, interruptions and what the user said next, edited files, and background commands. Read the pre-compaction and ⚑ lines carefully; they are the taste you would otherwise lose. If the script finds nothing (another agent, or no transcript), continue with your context.
2. **World state**: `git status`, `git log --oneline -15`, `git diff --stat`, uncommitted work. For anything that may still be running (background shells, `nohup`, `tmux`, Slurm `squeue -u $USER`, `nvidia-smi`), check it now rather than trusting the transcript: a job the transcript says was launched may have died.
3. **Your own context**: the reasoning behind decisions, current hypotheses, and what you were about to do.

## Step 2: Write the handover

Use the template in `references/template.md`. Give the session a short name of two or three words that the user would recognise tomorrow (what the work was about, e.g. `clip-sweep`, `reviewer-2-stats`), and save the handover as `.shift/<name>-YYYYMMDD-HHMM.md` in the project root, then copy it to `.shift/LATEST.md`. Tell the user that name at the end: it is all they need in order to pick the session up again. If the project is a git repo and `.shift/` is not ignored, add it to `.gitignore` and say so (handovers can contain private notes). Write in the language the user spoke in this session.

What makes a handover carry the soul rather than just the facts:

- **Name the files the next session must read, and make it a short list.** The standards you agreed on, the protocol, the spec, the data dictionary, the plan: a new session will not find them on its own, and summarising them in the handover both loses their detail and wastes context. So list them as required reading, one line each on what it governs, and let the next session read the file itself. Keep it to the few files that would change what it does; everything else goes under "reference, read if needed". Candidates: files you created or edited in this session (the transcript digest lists them), anything the user told you to follow, and the usual suspects in the repo (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, docs that read like a standard, protocol, spec or checklist).
- **Point, don't paste.** Never copy a file's contents, a long log or a code block into the handover when a path plus a line range says it better. A handover is read in full by the next session, so every paste is a tax on it; a path is three tokens and stays correct when the file changes.
- **Tiered, not flat.** Tier 1 goes first and is never skipped: status, the picture and mental map, next actions, no-go zones, and the taste table. Tier 2 (evidence ledger, experiment details, running jobs, gotchas, jargon) and Tier 3 (external pressure, file map, if–then plans) follow. Omit any section that has nothing real in it; an empty heading teaches the reader to skim.
- **Rejected paths carry their reason and a reopen condition.** "Tried X, failed" invites a retry; "Rejected X because Y; reopen only if Z" prevents one.
- **Record who the user is, not only what they corrected.** Facts the user mentioned about themselves in passing are easy to drop because they were never the task: their field and role, their tools, their situation and constraints, interests and plans, people they mentioned, and the date when any of these changed. A newcomer who knows the task but not the person gives generic answers.
- **Taste is behaviour, not adjectives.** "Be concise" is useless. "Answers ≤ 5 lines unless asked; never end with a recap. User: 'stop summarizing, just give me the conclusion'" is transferable. Record what you assumed, what the user corrected, the general rule, and the user's own words. See `references/taste.md`.
- **Tag every claim**: `[verified: command → result]`, `[assumed]`, or `[user said]`. The next session treats untagged claims as facts, and a hunch that reads like a fact is the most expensive thing a handover can pass on. `verified` is for observations (a number, an error, what a file contains), never for interpretations: "both runs hit NaN in layer 11" can be verified; "gradient explosion is the root cause" stays a hypothesis even when every observation fits it.
- **Keep the user's view the user's.** You are writing the handover, so your own conclusions will feel like the obvious ones. In the mental map, say whose hypothesis each one is. If the user proposed a hypothesis, it stays the working hypothesis unless they explicitly accepted another. Your competing view goes next to it, labelled as yours, with the user's stated evidence for and against kept intact. Quietly replacing the user's reading with the agent's is the most common way a handover loses its soul. This applies to the whole document, not just the mental map: the status line and the picture are read first and believed most, so they must not state as settled ("the root cause is X") what the mental map lists as an open hypothesis.
- **Mark what was superseded.** When a decision changed during the session (a different data file, a new analysis design, a number that turned out stale), record the final state *and* what it replaced: "use B (replaces A, which is dead because …)". The old version is still in the transcript, in old files and in commit messages, and a newcomer will find it.
- **Exact beats summarized**: the literal command, path, seed, job ID, number, and error message.
- **Keep what you told them, not only what they told you.** The user will come back to your own earlier answers: a number you reported, a ratio or setting you recommended, a name, a draft you wrote for them. A handover written from the user's side drops these, and the next agent then answers differently. Record the specifics of anything you told or produced that they may ask about again.
- **Pin times to dates.** "Two weeks ago" means nothing once the session is over. Convert relative time to an absolute date using when it was said, and keep the original words: "bought the amp around May 11 (said on May 25: 'two weeks ago')". Record when things started, ended and changed, so durations can be worked out later.
- **Write for a smart colleague with zero context**, not for yourself. If a sentence only makes sense to someone who was in the session (e.g. "the fix we discussed"), rewrite it.
- **Never copy secrets** (API keys, tokens, passwords). Point to where they live instead.
- **Stay inside a budget.** The next session pays for every line, so aim for under 200 lines, and treat anything longer as a signal that you are pasting file contents, narrating the session's history, or keeping sections that have nothing real in them. A handover that costs more to read than the work it saves is a bad trade.

### When the session is about to be cut off

If the usage limit has been hit or is close, the context is nearly full, or the user says they must stop now, treat the handover as the only thing that matters: **write the file first**, in one pass, Tier 1 only, and skip the exam and every subagent (they cost what you no longer have). Save it, tell the user the session name and the limit's reset time if one was printed, and stop. A short handover that exists beats a thorough one that was still being written when the session died. The next session can run `shift-recover` or `shift-start` and improve it.

## Step 3: The exam (the I-PASS readback)

Skip only if the user said `quick`, or if the session is being cut off as above. Follow `references/exam.md`. In short:

1. Write 8–12 questions **from the session, not from the handover**, together with an answer key that stays in your context and is never written to the file. Cover Tier 1 first: taste choices ("the user asks for X: do you do A or B?"), no-go zones, the next action and its done-condition, verified vs assumed, then Tier 2 (jargon, running jobs, gotchas). Whenever the user stated a hypothesis or judgement, ask what *the user* thinks, and key it by quoting their messages rather than from your own understanding, which shares the handover's blind spots.
2. Spawn a **fresh subagent** that gets only the handover path, read access to the repo, and the questions. It is not allowed to read transcripts, `~/.claude/`, or older handovers, and it must answer "NOT IN HANDOVER" rather than guess.
3. Grade against your key. For every miss, fix the handover where the information belongs (not an FAQ appended at the bottom), then re-examine the missed points with rephrased questions on a new subagent. At most 2 patch rounds.
4. Put the result in the footer: `Handover fidelity: 11/12 (after 1 patch round)`, and list any gaps you could not close.

If you cannot spawn subagents in this environment, do a strict self-check against the questions instead and tell the user that the exam did not run with a fresh reader.

## Step 4: Keep the durable taste

Some corrections apply only to this task; others are how this user always works. Using `references/taste.md`, list the durable ones separately and ask the user whether to save them, and where: this project's `CLAUDE.md`/`AGENTS.md`, or their user-level one for all projects. Read the target file first and merge, don't duplicate. Write only what the user approves.

## Step 5: Report

Tell the user briefly: the session name, where the handover is, the fidelity score, what the exam caught and how it was fixed, and any gaps left. End with the line to start the next session:

> New session: run `/shift-start` and confirm the name **<name>** (or say "pick up <name>").

The receiving session deletes the handover once it has been picked up, so `.shift/` only ever holds work that is still waiting.

## Gotchas

- **The transcript expires.** Claude Code deletes old session files (around 30 days by default), and `mine_transcript.py` can only mine what is still on disk. If it finds nothing, say so instead of implying the corrections were checked.
- **Compaction has already happened by the time you notice.** Lines marked `[pre-compaction]` in the digest are *not* in your context; trust the digest over your memory for anything early in the session.
- **Your own conclusions feel like facts.** You lived the session, so what you inferred reads as settled. Check the status line and picture against the mental map before finishing.
- **Secrets hide in commands.** A command you paste as "exact" may carry a token or a private URL. Scan what you copy.
- **The exam only tests what your answer key knows.** Keys about the user's views must quote the user, or the exam will confirm your own misreading (this happened: see the project CHANGELOG).
- **Background jobs lie.** A job the transcript says was launched may have died; check it rather than copying the claim.

## When not to use this

- The session is short and nothing subtle happened: just continue, or rely on `/compact` if you stay on the same task.
- The work is going to another person rather than your next session: use `shift-brief`, which packages files and tests the bundle.
- The previous session already ended without a handover: that is `shift-recover`, which rebuilds the state instead of writing one from a context it no longer has.
- The user wants a status report for someone else (an advisor, a team). A handover is written for the next agent, not for an audience.
