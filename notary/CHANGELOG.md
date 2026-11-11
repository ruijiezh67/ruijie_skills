# Changelog

Every rule traces to a real failure. Record the failure next to the fix.

## 0.2.2 (2026-11-11): third review of awesome-llm-apps PR #1270
- A 1900 to 2100 integer with a unit (2000ms, 2048MB) is no longer skipped as a year.
- Receipts with a missing, empty or duplicate id are a BAD turn.json line, so a failed receipt cannot be masked by a later one with the same id.
- Limits: k and M are units, not multipliers.
- Tests: 26.

## 0.2.1 (2026-11-08): second review of awesome-llm-apps PR #1270
The maintainer read the checker adversarially and found three ways an unreceipted number could get out.
- **Footer laundering:** any line starting with 🧾 or "Receipts:" was skipped, so "Receipts: test accuracy 91.0%" passed. Now only the exact footer line is skipped.
- **Percent scaling without %:** any source of magnitude 1 or less also matched x100, so 0.85 passed against "lr": 0.0085. Now x100 applies only when the reported value carries %.
- **Units:** `3985s`, `1.2GB`, `250ms` and `0.5x` were invisible. Unit suffixes are now read (not converted), so these need receipts, and a quote "elapsed 66.4s" backs 66.4.
- A receipt id that is not a string is now a BAD line, not a traceback.
- Limits are documented: exit codes and sessions are not checked.
- `run_drift.py` now pins `--model claude-opus-5-5`.
- 4 new tests (25 total); each fails on 0.2.0.

## 0.2.0 (2026-11-06): review of awesome-llm-apps PR #1270
Each item below is a gap the maintainer found between the docs and the script.
- **`cmd` receipts now match the command.** Before, `command` was never compared with the log, so a quote from any tool output passed (a number from `cat old_notes.txt` satisfied a receipt for `python never_ran.py`). The quote must now be in the output of a logged command equal to `command` (whitespace normalized).
- **Expiry docs say what the code does.** Expiry only sees files named in the command. A script that opens `preds.csv` internally never expires, so the skill tells the agent to pass input files as arguments.
- **`user` receipts without a transcript are `??` unchecked, not `ok`.** Only the Stop hook, or `check --transcript`, can verify them.
- **The receipt threshold is documented, and `check --all` exists.** By default, integers from 1 to 99 need no receipt.
- **No tracebacks.** `calc` constants are floats, so `9 ** 9 ** 9` overflows at once instead of running for hours, and the OverflowError is a BAD line. A malformed `turn.json` is a BAD line too. A calc with `1e6` no longer reads `e6` as a receipt id.
- **README is plain about the hooks.** The Stop hook checks every reply wherever it is installed, and `log.jsonl` stores full Bash output, so add `.notary/` to `.gitignore`.
- **The drift eval is re-runnable** from `agent_skills/evals/notary/drift/` in the PR (fixture generator, scenario, standalone runner). It was re-measured with this version.
- **Tests:** 21 deterministic tests.
- **Description:** the Chinese trigger phrases were removed. All project files are now English only.

## 0.1.0 (unreleased, 2026-10-27)
- `notary` skill: a receipt for every number (`file` / `cmd` / `calc` / `user` / `na`), honest rounding, N/A instead of 0 for anything unmeasured.
- `notary.py`: one stdlib script. `check` verifies receipts and coverage. `hook-log` (PostToolUse) logs real tool output so `cmd` quotes cannot be invented. `hook-stop` (Stop) sends a reply back once when it states an unbacked number. Hooks fail open and never loop.
- `evals/test_notary.py` (then `bench/test_notary.py`): 14 deterministic tests.

- **Receipts expire.** A `cmd` receipt now fails when a file named in its command changed after the output was logged. The first benchmark round showed why. On single-turn summaries Opus 5.5 avoided every planted trap even with no skill, so the failure that matters is across turns: a number computed earlier, and a file that changed since. Before this, a stale output still carried a valid-looking receipt. Added mid-way through the first full benchmark run, so the last runs of that batch used the newer checker. The change only adds a failure mode, and none of the single-turn scenarios modify files after reading them.

### Findings from the drift benchmark (two turns, a run silently re-done in between)
- **Headline (n=6 per arm).** These counts are runs that reported aug's pre-re-run accuracy as current:
  - no skill: 6/6;
  - the one-line instruction "every number must come from a file you read or a command you ran in this session": **6/6**;
  - notary skill without hooks: 1/6;
  - notary skill + hooks: **0/6**, at about 2.6× the cost ($0.71 vs $0.27 median).

  The instruction fails for a structural reason, not a wording one. The stale number *did* come from a command run in this session. Only an expiry check notices that the command's input changed afterwards.
- **Skill without hooks: `cmd` receipts can never verify.** With no PostToolUse hook there is no `.notary/log.jsonl`. The agent saw 7 of 12 receipts fail, explained why in its reply, and sent the stale numbers anyway. **Fixed after the benchmark:** `notary.py run -- <cmd>` logs a command's real output without hooks, and the skill tells the agent to use it when `.notary/log.jsonl` is missing. Re-measured after the fix: skill-only is still 1/6. The 5 runs that used the skill all logged their commands through `run`, and the one miss never invoked the skill at all (no receipts written). The remaining gap is triggering, which is what the hooks close.
- **Scientific notation was unreadable.** `1.0e-4` could not be parsed, so an agent dropped the learning rates from its summary rather than leave them unreceipted. **Fixed:** e-notation in `numbers()` and `parse_value()`. 17 tests pass.

### Findings while building the benchmark
- **The benchmark operator's own setup leaks into every arm.**
  - The first smoke runs used the shared harness, which did not isolate the host. Asked directly, a `claude -p` session quoted the operator's global `~/.claude/CLAUDE.md`. That file contains the rule "write N/A for unmeasured data, never 0", which is notary's rule 2, so it was present in the "no skill" arm too.
  - `--setting-sources project` hides user skills and plugins, but **not** the user CLAUDE.md. Only `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` removes it.
  - `--disable-slash-commands` also removes the skill under test, so it cannot be used.
  - The harness now has `isolate=True` (all of the above plus `--strict-mcp-config --no-session-persistence`). The two contaminated runs were deleted.
  - **The runcard and shift-change benchmark results were produced without this isolation and should be re-run before they are published.** (Credit: caveman's eval README documents the same leak for plugins.)
- **The first judge counted a warning as an escape.** A reply that said "the README table is out of date: it shows 0.884 / 0.913" was scored as reporting stale numbers. Trap rules now skip lines that flag the problem (`unless_line`).
- **Pairwise arithmetic over every number in a repo explains almost any number.** The "unbacked" count first allowed differences and ratios between all source numbers, so a made-up "1.4 hours" was explained. It now allows them only between key metrics. It is still lenient, so it undercounts fabrication rather than overcounting it.
