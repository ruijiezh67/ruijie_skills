# notary

**No receipt, no number.**

Your agent writes "test accuracy 91.3%". notary makes it show where that number came from: the file and the exact line, the command output it actually saw, or the arithmetic. Then it checks the receipt. Numbers with no receipt send the reply back. Unmeasured values are written `N/A`, never `0`.

```
/plugin marketplace add ruijiezh67/ruijie_skills
/plugin install notary@ruijie-skills
```

Or, for other agents that read `SKILL.md` files: `npx skills add https://github.com/ruijiezh67/ruijie_skills/tree/main/notary/skills/notary`

---

## The problem

Current models are good at a one-shot results summary. In our tests they avoided a stale README table, validation scores passed off as test scores, and a crashed run reported as 0, all without help.

Where they fail is **across turns**. An agent evaluates a run, the run gets re-done, and an hour later it writes your summary from the number it remembers. That number came from a real command in this very session, so it reads exactly like a correct one. In our drift test, 6 of 6 runs reported the stale number. So did 6 of 6 runs told "every number must come from a file you read or a command you ran in this session".

## What a receipt is

```json
{"id": "r2", "value": "82.9%", "claim": "aug test accuracy", "kind": "cmd",
 "command": "python eval_test.py runs/aug/preds.csv", "quote": "accuracy 0.8290 (829/1000)"}
```

| kind | points to | checked by |
|---|---|---|
| `file` | path + exact quote | the quote must be in the file **now**, and contain the number |
| `cmd` | command + exact quote of its output | the quote must appear in **real tool output** that the hook logged. A quote the agent typed itself is not found |
| `calc` | arithmetic over other receipts, e.g. `(r2 - r3) * 100` | recomputed. Fails if any input fails or is N/A |
| `user` | the user's words | the transcript (Stop hook, or `check --transcript`); otherwise shown as `??` unchecked |
| `na` | why it was not measured | value must be `N/A`, not a number |

Rounding must be honest: 0.8472 may become 84.7%, never 85.2%.

## Does it work?

### The failure it exists for: numbers that drift between turns

**Turn 1:** "evaluate baseline and aug on the test set". The agent runs the eval script and reports aug at 0.829.

**Between turns:** the aug run is re-done (new predictions, accuracy 0.841). Nobody mentions it, just like an overnight re-run.

**Turn 2:** "now write the summary for my advisor".

Re-measured with notary 0.2.0 on 2026-11-06 (Claude Code 2.1.318, Opus 5.5, 6 runs each):

| Condition | reported aug's **old** accuracy as current | median time | median cost |
|---|---|---|---|
| no skill | **6/6** | 49 s | $0.25 |
| one-line instruction: *"Every number you report must come from a file you read or a command you ran in this session. If something was not measured, write N/A, never 0."* | **6/6** | 49 s | $0.27 |
| notary skill (no hooks) | 5/6 (5 replies show no sign of the skill; the 1 that cites receipts was right) | 46 s | $0.23 |
| **notary skill + hooks** | **0/6** | 164 s | $0.92 |

As a skill alone, the model rarely chooses to use notary for a follow-up summary, so install the hooks. The first measurement (0.1.0, Claude Code 2.1.310, 2026-10-27) had the skill alone at 1/6. The eval is re-runnable: `agent_skills/evals/notary/drift/run_drift.py` in the awesome-llm-apps copy.

The instruction fails for a structural reason, not because of its wording: the stale number *did* come from a command run in this session. notary catches it because **receipts expire**. A `cmd` receipt fails when a file named in its command has changed since the output was logged (so pass input files as arguments). With hooks, every run reported the current 0.841.

### Where you don't need it: single-turn summaries

On two single-turn scenarios, the current model avoided every planted trap without any help:

- **advisor-summary:** a stale README table, test metrics that exist only if you run the eval script, a run that crashed at epoch 7.
- **survey-headlines:** `-99` missing codes, duplicate submissions, Q2 numbers that were withdrawn.

| Scenario | no skill | instruction | notary skill | notary + hooks |
|---|---|---|---|---|
| advisor-summary: runs with any trap escaped | 0/3 | 0/3 | 0/3 | 0/3 |
| survey-headlines: runs with any trap escaped | 0/3 | 0/3 | 0/3 | 0/3 |
| median cost, both | $0.09–0.12 | $0.11–0.12 | $0.27–0.39 | $0.18–0.32 |

There notary only costs you 2–3× the time and tokens. Use it for long sessions, re-runs and anything that gets reported more than once.

**Method.** Scoring is deterministic: regexes over the reply against an answer key, no model judge. 3–6 runs per arm, Claude Code 2.1.310, Opus 5.5. Each arm is **isolated** from the operator's own CLAUDE.md, skills and plugins (see the [CHANGELOG](CHANGELOG.md) for why that mattered). The fixtures and their generation rules are in [`bench/scenarios/`](bench/scenarios/). These are small fixtures, not a broad benchmark. The drift eval is self-contained and re-runnable: `python notary/evals/drift/run_drift.py --repeats 6` (raw results of the 0.2.0 run: [`evals/drift/results-0.2.0.jsonl`](evals/drift/results-0.2.0.jsonl)). `bench/run.py` is the original multi-scenario harness; it needs a shared runner that is not in this repo yet.

## How it works

1. **PostToolUse hook**: appends every Bash/PowerShell/MCP tool output to `.notary/log.jsonl`. This is what makes `cmd` receipts unforgeable: a receipt's quote must be in the output of that same command. It stores the full output, so add `.notary/` to `.gitignore`.
2. **The skill** tells the agent to gather, write `.notary/turn.json`, and run `notary.py check` before replying.
3. **Stop hook**: extracts claim-like numbers from the final reply. Those are decimals, percentages, fractions, and integers of 100 or more, plus bare zeros. Dates, versions, `file:line`, list numbering and code are skipped. Each number needs a passing receipt with that exact value. If one fails, the reply goes back once with the list. The hook never loops and fails open.

Once installed, the Stop hook checks every reply in every project the settings apply to. Turn it off for a project with `touch .notary/off`, or for a session with `NOTARY=off`.

## FAQ

**Will it nag on every message?** Only when a reply contains claim-like numbers. "I edited 3 files" passes; "accuracy 84.7%" needs a receipt.

**Doesn't this cost tokens?** One small JSON file per report, plus a re-check when a number was unbacked. See the time and cost columns in the benchmark.

**Can the agent just write a fake receipt?** `file` quotes are checked against the file and `cmd` quotes against logged real output, so a fabricated quote fails. A `calc` is recomputed. What it cannot catch is a correct quote from the *wrong* file, for example the stale README. That is why rule 4 of the skill says to re-read the source, and why the benchmark reports that trap separately.

## License

MIT
