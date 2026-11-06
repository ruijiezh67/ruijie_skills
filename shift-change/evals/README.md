# Evaluations

Anthropic's skill best-practices checklist asks for "at least three evaluations" per skill, tested on Haiku, Sonnet and Opus, and warns that a description which is too broad causes false triggers while one that is too narrow never fires ([best-practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), [skill-creator post](https://claude.com/blog/improving-skill-creator-test-measure-and-refine-agent-skills)).

Two things are measured here, and they are different:

1. **Triggering** — does the right skill fire on natural phrasing, and stay quiet on near-misses? Cases below, both positive and negative.
2. **Output quality** — does the handover carry what the next session needs? That is what [`../bench/`](../bench/) measures, against popular alternatives and on LongMemEval.

## How to run

- `claude plugin eval` (Claude Code; needs a build that has the subcommand: check `claude plugin --help`). Run `claude plugin eval init` in this plugin root to generate the case files in the version your CLI expects, then port the cases below. Each case runs three times; a case passes when its score meets `--threshold` (1.0 by default), and the `WITH` / `W/OUT` arms show whether the skill is what made it pass.
- `skill-creator` (plugin): its `scripts/run_loop.py` optimises a description against a trigger eval set, and `eval-viewer/generate_review.py` renders outputs for human review.
- By hand: run each prompt in a fresh session with the skills installed and check the expectation.

## Trigger cases

Positive cases must fire the named skill; negative cases must not fire any of the four.

| # | Prompt | Must happen |
|---|---|---|
| T1 | "I'm done for today, my context is nearly full — save everything so tomorrow's session isn't lost." | `shift-change` fires; a file appears under `.shift/` |
| T3 | "Pick up where we left off." (a handover exists in `.shift/`) | `shift-start` fires; it reads the required files and waits for confirmation instead of starting work |
| T4 | "Package the tokenizer ablation for my labmate who has cluster access." | `shift-brief` fires; a bundle directory with BRIEF.md and START_HERE.md appears |
| T4b | "We hit the limit yesterday and I never handed over — what was I doing?" | `shift-recover` fires; it lists recent sessions and asks which one |
| T4d | "Pick up where we left off." with a handover present in `.shift/` | `shift-start` fires, **not** `shift-recover` |
| T5 | "Summarise this file for me." | none of the four fires |
| T6 | "Write a handover doc section in the paper about the clinical handoff literature." | none fires: the word "handover" appears, but the task is writing prose about a topic |
| T7 | "/compact" | none fires: compaction is a different thing and the user asked for it by name |
| T8 | "Hand me the output of that script." | none fires (near-miss on "hand") |

## Output cases

| # | Setup | Expectation |
|---|---|---|
| O1 | A session where the user corrected the agent twice and rejected one approach, then `/shift-change quick` | the handover contains a taste table with the user's own words, and the rejected path with a reason and a reopen condition |
| O2 | A session that agreed on a standards file, then `/shift-change` | the standards file is listed under "Read these first" and its content is **not** pasted into the handover |
| O3 | `/shift-change` with the exam on | the footer reports a fidelity score, and any patch round is named in the report |
| O4 | `/shift-start` on a handover whose required file was deleted | it says the file is missing in the readback instead of proceeding |
| O5 | `/shift-recover` on a session that launched a background job | the readback states whether the job finished, with the log or exit status as evidence, not "it was running" |
| O6 | `/shift-change` while the usage limit is in force | the file is written Tier 1 only, no exam, no subagents, and the reply names the reset time |

Regressions found in real use belong in [`../CHANGELOG.md`](../CHANGELOG.md) with the fix; a case here should exist for each.
