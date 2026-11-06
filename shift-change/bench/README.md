# Handover fidelity benchmark

**Question:** after a handover, does the next agent know what the previous session knew, including the things that never show up in the code: the user's taste, the rejected paths, what is still running, what is only assumed?

## Method

1. **Scripted research sessions** (`sessions/<name>/`). A seed repository plus a list of user turns, replayed with `claude -p` to produce a *real* Claude Code session. The turns plant specific facts across categories: taste corrections, rejected paths with reasons, project jargon, a job running on a cluster, environment gotchas, a hypothesis with evidence for and against, verified vs assumed claims, the next action, and external pressure. A `/compact` in the middle pushes the early facts out of the live context, the way a long real session does.
2. **Conditions** (`conditions.json`). Each condition forks the same finished session (`--resume <id> --fork-session`) and produces a handover its own way: nothing at all, Claude Code's `/compact` summary, two popular open-source handoff skills (pinned by commit at run time), and this repo's `shift-change` with and without its exam.
3. **Exam.** A fresh agent that never saw the session gets only the handover and read access to the repository, and answers a held-out question bank (`questions.json`). The skill under test never sees these questions. Its own exam writes different questions from the session.
4. **Grading.** An LLM grader scores each answer against the key: 1 / 0.5 / 0.

All runs set `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, so no condition can leak facts to the exam through memory files. The repository is reset to the same commit before every handover and every exam.

## Second benchmark: LongMemEval (official data)

Sessions we write ourselves can always be accused of suiting the skill we wrote. So the same comparison also runs on **LongMemEval** (Wu et al., ICLR 2025, MIT licence), using the parts that are not ours to choose:

- **Histories**: the official chat sessions, written verbatim into a resumable Claude Code transcript. No turn is generated or edited. Each question keeps all of its evidence sessions plus a seeded sample of its own distractor sessions, capped at ~100k characters (`--chars`), original order preserved.
- **Questions and answers**: the official ones, including the preference, knowledge-update and abstention types, which map onto what a handover is supposed to carry (taste, superseded decisions, knowing what it doesn't know).
- **Prompts**: the official reading prompts from `run_generation.py` and the official per-type judge prompts from `evaluate_qa.py`, copied verbatim.
- **Dev/test split**: the skill was improved only against the dev sample (seed 2025); reported numbers come from a disjoint test sample (seed 2026). The skill version is pinned in each result file (`pins`).
- **Extra condition** `full-history`: the answering agent reads the whole capped history. This is the upper reference, and handovers are not expected to beat it.

Deviation to state plainly: the official judge model is gpt-4o; here the same prompts run on Claude. Scores are therefore comparable across conditions in this table, not with numbers published elsewhere.

```bash
python longmemeval.py --split dev  --jobs 2     # for improving the skill
python longmemeval.py --split test --jobs 2     # the reported run
python longmemeval.py --split test --summarize
python chart.py                                  # figure for the README (needs matplotlib)
```

The first run downloads `longmemeval_s_cleaned.json` (277 MB) into `.work/data/`.

## Run it (scripted sessions)

```bash
python run.py --session ml-divergence --repeats 3      # one session, all conditions
python run.py --conditions none,shift-change            # a subset
python run.py --summarize                                # rebuild results/summary.md
```

Runs are cached in `results/<session>/runs/`; delete a file to rerun it. A full run costs real tokens: each condition replays a handover and two short calls per session and repeat.

## Limits, stated up front

- The sessions are synthetic. They are designed to resemble real research sessions, but planted facts are cleaner than real ones.
- The same model family writes, takes and grades the exam. Scores are comparative across conditions, not absolute.
- `shift-change` spends extra time and tokens on its exam; the summary reports handover time next to the score so the trade-off is visible.
- Questions were written before any results and have not been edited since. One of them, ml-divergence q8 ("the current leading hypothesis"), turned out to be ambiguous: the user states one hypothesis and then acts on the agent's. No condition scores well on it. It stays in the table as pre-registered; see `../CHANGELOG.md`.
- Runs that failed for infrastructure reasons (usage limits, a hung process, an empty reply) are not scored; they are kept in `results/<session>/failed/` and re-run, and the summary lists them.
