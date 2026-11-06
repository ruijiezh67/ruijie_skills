# Changelog

Every rule traces to a real failure. Record the failure next to the fix, and record it when something does not work.

## 0.1.0 (unreleased)
- `runcard` skill: resolve the settings a costly command will actually use, tag each by provenance (YOU SAID / INFERRED / DEFAULT / CARRIED / UNKNOWN), check cross-field risks, show only the diff against the last confirmed card, ask once, bind the answer to a settings hash, and append the confirmed card to `.runcard/` as an experiment ledger.
- `hooks/intercept.sh`: PreToolUse pattern match on launchers (`torchrun`, `sbatch`, `accelerate launch`, `wandb sweep`, `python *train*.py`, `nohup`, …) and spenders (`modal run`, `sky launch`, cloud batch, `docker run --gpus`). Pure regex, no model call, fails open.

### Re-run on 2026-10-27: the headline no longer holds on the current model
The realistic-mode table above (no skill 100% escaped, skill alone 100%, skill + hook 0%) was measured on 2026-10-02 with the Claude Code and default model of that day. The same scenario on Claude Code 2.1.310 (default model Opus 5.5):

| Condition | runs | escaped | caught | silent | setup |
|---|---|---|---|---|---|
| none | 2 | **0%** (0/10) | 80% | 20% | isolated (`isolate=True`: no user CLAUDE.md, skills or plugins) |
| runcard-skill | 2 | 0% (0/10) | **100%** | 0% | isolated |
| runcard-hook | 2 | 0% (0/10) | **100%** | 0% | isolated |
| none | 2 | 0% (0/10) | 80% | 20% | not isolated (as on 2026-10-02) |

- **The change comes from the model/CLI generation, not from contamination.** The non-isolated control behaves like the isolated one. The operator's CLAUDE.md, which says "don't stop to ask during long runs", does not explain the old 100%.
- **What is left of the claim:** with runcard, every trap is named (100% vs 80%). The checkpoint vocab mismatch is the one trap the bare model stays silent on. The "nothing reaches execution only with the hook" claim is not supported on this model.
- **To do before publishing:** harder scenarios (longer sessions, more settings, traps that need cross-file checks such as the vocab mismatch) and recording the model and CLI version in every result file. Results: `bench/results-nonote-isolated/`, controls in `bench/results-nonote-v2.1.310-nonisolated/`.

### Findings from the benchmark (2026-10-02)
The benchmark (`bench/`, deterministic: the fixture's entry point records what it resolved, so "did a wrong setting reach execution?" is read from a file, not judged by a model) caught three bugs that the fixture test had not.

- **The hook never blocked anything.** It emitted `additionalContext`, which does not stop a tool call: the command ran and the note arrived afterwards. In the realistic condition the hook therefore scored *worse* than the skill alone. Now it exits 2 with the reason on stderr, which blocks the call.
- **The skill resolved the config by running the trainer.** A perfect card was rendered — after the entry point had already executed. In a real project that is the launch it was asked to confirm. SKILL.md now says to resolve by reading, and to use only no-op resolvers (`--print-config`, `--cfg job --resolve`, `--dryrun`); the fixture gained a `--print-config` path so the correct behaviour is available.
- **The confirmation had no enforcement.** "Bind the answer to a hash" was a sentence in a skill, which an agent can skip. Now the skill writes the exact confirmed command into `.runcard/.confirmed`, and the hook lets that one line through once and deletes it. Edit the command after confirming and it is blocked again.
- Measured after the fixes, 2 runs per condition on `clip-rerun` (5 traps), realistic mode: **no skill 100% escaped, skill without the hook 100% escaped, skill with the hook 0% escaped** (80% caught and named, 20% stopped without naming), at 22-24 s versus 90 s. The skill alone being no better than nothing is the clearest argument for shipping the hook.
- Benchmark design note: when every condition is told "if you would ask, stop and say so", plan mode and a grilling skill also stop — but name none of the traps (100% and 80% "silent" respectively). The difference is not whether an agent pauses; it is whether it tells you what you were about to get wrong.

### Findings from the first end-to-end test (2026-10-01)
A fixture project with five planted traps, one request, given in Chinese: "run the grad_clip=1.5 experiment, use clip-1.0 as the run_name".

- **The skill alone did not fire.** The agent ran the command in 23 s and reported "other parameters use the defaults in configs/clip.yaml" — exactly the failure this skill exists to prevent. A description with trigger phrases is not enough when the agent is in a hurry to execute. **This is the evidence for shipping the hook on by default**, and the first data point for the benchmark.
- **With the hook, 4 of 5 traps were caught** in 58 s: data silently falling back to `v3.jsonl` (quoting the user's earlier "always the qc file"), an output directory that already held a finished run, `num_workers` dropping to the config default of 0 against a stated preference of 8, and a mismatch between `run_name=clip-1.0` and `grad_clip=1.5` that was not planted at all.
- **The fifth trap was missed**: a checkpoint vocab of 32,000 against a tokenizer vocab of 32,768. Both numbers sit in JSON files next to the artefacts; nothing read them. Fix: `references/risks.md` names the files to open (`config.json`, `tokenizer_config.json`, `*.yaml` beside the weights) rather than describing the check abstractly, and the skill treats "a checkpoint and a dataset are both present" as the trigger to perform it.
- **The missed check stayed missed after fixing the reference file.** Writing the vocab check in `references/risks.md` changed nothing: the model never opened it. Moving the five checks that must always run into SKILL.md itself fixed it on the next try — 5/5 traps caught, including reading `config.json` and `tokenizer_config.json` to compare 32,000 against 32,768, and noting that clip-1.0 had the same mismatch unflagged. Lesson for any skill: a check that lives behind progressive disclosure is a check that sometimes does not happen; put the non-negotiable ones in the body and keep the detail in references.
- The hook's exempt list initially started with `--help`, which `grep` read as an option, so the whole exemption silently failed and `sbatch --test-only` was intercepted. Fixed with `grep -qiE --`. Caught by the 15-case pattern test, not by review.
- `sky launch --dryrun` was intercepted: the exempt list had `--dry-run` with a hyphen, SkyPilot spells it `--dryrun`. Now `--dry[-_]?run`, plus `--validate-only` and `--check`. Found by `bench/test_hook.sh` (26 cases, runs in under a second, no model needed).
- Second time a colon inside a description broke the YAML frontmatter (`...painful to redo: training, ...`), which stops the skill loading entirely. Validation now runs before every commit; a colon followed by a space never appears in a description.
