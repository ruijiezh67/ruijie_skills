# Changelog

Every rule in the skills should trace back to a real failure. Record the failure next to the fix, and record it when a fix turns out not to be measurable.

## 2026-11-12: LongMemEval re-measured with isolation
- **Results:** every arm now runs isolated from the operator's own setup (no user CLAUDE.md, skills, plugins or MCP servers), on Claude Code 2.1.322. shift-change scored 20/21, tied with shift-change quick, `/compact` and REMvisual. Paired against `/compact`: 1 win, 1 loss, 19 ties. Against mattpocock `handoff`: 4 wins, 0 losses.
- **The September lead is gone.** That run was not isolated and gave 17/21 against `/compact`'s 14/21. It is kept in `bench/results-longmemeval/` and marked as superseded in the README.
- **Harness changes:**
  - `claude()` isolates by default.
  - Session transcripts are kept only where a later step resumes them, and are deleted after each run.
  - The work and results directories can be moved off the system disk (`SHIFT_BENCH_WORK`, `SHIFT_LME_RESULTS`).
  - Every usage-limit message now stops new runs. The old check only matched "hit your limit", so a "5-hour limit" reply was recorded as 51 failed runs, which were then re-run.

## 0.1.0 (unreleased)
- `shift-change`: I-PASS handover template (tiered), transcript mining for corrections lost to compaction, fresh-agent exam with patch rounds, durable-taste proposal.
- `shift-start`: world check + readback, waits for confirmation.
- `shift-brief`: dependency tracing, sanitizing, runnable acceptance criteria, cold-start test by a fresh agent.
- `bench/`: handover fidelity benchmark against no handover, /compact, and six popular open-source handoff skills.

### Fixes from the benchmark, in order
1. **Agent's view promoted over the user's** (pilot, ml-divergence q8). The handover listed the agent's hypothesis (gradient explosion) as "H1, verified, against: none" and demoted the user's hypothesis (fp16 overflow) along with the user's own counter-evidence. Added: `verified` is for observations, not interpretations; the mental map says whose hypothesis each one is and keeps the user's working hypothesis unless they accepted another.
2. **The self-exam shared the writer's blind spot** (same pilot run). shift-change's own exam scored itself 11/11 and missed item 1, because the agent wrote the answer key from its own understanding. Exam keys for the user's views must now be quoted from the user's messages, and a "whose view" question is required whenever the user stated a hypothesis or judgement.
3. **Superseded decisions** (survival-revision). `/compact` kept the new sensitivity-analysis design but not that the old one had been dropped. Added: superseded decisions and stale numbers are recorded together with what replaced them.
4. **Top of the document contradicting the mental map** (formal run, ml-divergence, 6/6 handovers). After fix 1, handovers correctly labelled "H1 (user's working hypothesis)" and "H2 (agent's view, not accepted)", yet the status line and picture above still said "root cause located: grad_clip: null". Added: status and picture may not state as settled what the mental map lists as open.

5. **Who the user is** (LongMemEval dev set, question 35a27287). The handover recorded the user's corrections but reduced their personal context to a topic list ("French/Spanish language learning"), so the next agent answered a personalised request generically. Added an "About the user" block: facts the user shared about themselves, dated when they change. Changes are developed on a dev sample of LongMemEval and reported on a disjoint test sample.

6. **The agent's own answers and relative dates** (LongMemEval dev set: 0/3 on questions about what the assistant had said, 1/3 temporal). Handovers kept the user's side and dropped specifics the agent itself had given (a study's sample size, a dilution ratio, a detail of a story it wrote), and stored "two weeks ago" instead of a date. Added: record what you told or produced for the user, and pin relative times to absolute dates.

### Surviving an interrupted session (2026-10-01)
- New skill **`shift-recover`**: rebuilds the state of a session that ended without a handover (usage limit, crash, closed laptop, forgotten `/clear`). It lists recent sessions so the user confirms one by name, mines that transcript for the last intent, corrections and in-flight work, then checks what actually finished (git state, background and cluster jobs, partial outputs) and separates done / partly done / not started before proposing how to resume.
- `shift-change` gained a cut-off path: when the usage limit is hit or the context is nearly full, write the file first, Tier 1 only, no exam and no subagents, and report the reset time. Written while hitting the limit three times during the LongMemEval runs.
- `mine_transcript.py` gained `--list` (recent sessions: id, span, prompts, opening line) and accepts a bare session id for `--session`.

### Standards audit (2026-10-01, against the official docs: `docs/standards.md`)
- Descriptions rewritten in **third person**. The docs are explicit: "Always write in third person… inconsistent point-of-view can cause discovery problems." Ours opened imperatively.
- `<this-skill-dir>/scripts/...` replaced with `${CLAUDE_SKILL_DIR}` (documented variable) plus a relative fallback for other agents; the placeholder resolved to nothing.
- **Gotchas** sections added to all three skills; the Claude Code team calls this "the highest-signal content in any skill".
- `evals/README.md` added with 8 trigger cases (positive, Chinese, and near-miss negatives) and 4 output cases. Not yet executed: the installed CLI has no `claude plugin eval`.
- Plugin manifest now passes `claude plugin validate`: the root `$schema` and `description` keys were rejected as unrecognised; description moved to `metadata.description`.
- Caught by validation, not by review: a colon inside a quoted trigger phrase in `shift-brief`'s description broke the YAML frontmatter, which would have stopped the skill from loading at all.

### Token cost
- Handovers point at files instead of pasting them, and list required reading as paths: the next session reads the standard itself instead of a lossy summary of it. This fixes "the new session never opened the files we agreed on" and removes the largest source of handover bloat at once.
- Explicit budget: aim under 200 lines; the transcript digest cap dropped from 30k to 20k characters.
- Measured always-in-context cost of the three descriptions: 2,223 characters (~560 tokens).

### Workflow
- Handovers are named after the session (`.shift/<name>-<date>-<time>.md`), so picking one up means confirming a name, not a path.
- `/shift-start` deletes the handover it consumed (and the `LATEST.md` copy) once the user confirms the readback, so `.shift/` only holds sessions still waiting. Durable preferences are offered for `CLAUDE.md` first; a handover the user is only browsing is kept.

### What the benchmark does *not* show (yet)
- Fixes 1, 2 and 4 target a failure that is visible in the documents, but they did not measurably change scores. In the formal runs (3 repeats of every condition), ml-divergence q8 did not separate any methods: every condition scored 0–0.5, including no handover (mean 0.33). The pilot's 1.0 for no handover did not replicate.
- On inspection q8 is ambiguous: the user stated fp16 overflow as their hypothesis, but then launched a gradient-clipping sweep, which fits the agent's reading. The cleaner test, survival-revision q12, where the user disagrees with the agent explicitly, was answered correctly by nearly every method, shift-change included. A discriminating test of "whose view survives" still needs a new, pre-registered session.
