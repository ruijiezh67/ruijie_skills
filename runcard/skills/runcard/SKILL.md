---
name: runcard
description: Shows exactly what an expensive command will run with, before it runs. Resolves every setting the command will actually use from the command line, config files, environment and any project resolver, tags each value by where it came from (the user said it, it was inferred, it is a framework default, it was carried from the last run, or it is UNKNOWN), flags cross-field risks such as a checkpoint that does not match the dataset or an output directory that would be overwritten, shows only what changed since the last confirmed run, and asks once before launching. Use before any command that costs real time or money or would be painful to redo, such as training, fine-tuning, evaluation, sweeps, cluster submissions, cloud jobs, bulk API runs and large downloads. Triggers include "run the training", "launch the sweep", "submit the job", "start the experiment", "show me the run card", "what settings will this use".
compatibility: no dependencies; reads config files and runs a project's own resolver (e.g. Hydra, accelerate) when one exists.
---

# runcard

An agent that is about to spend two GPU-hours has resolved dozens of settings, and the user has seen maybe three of them. The rest come from config defaults, from an earlier run, or from the agent's own guess. That is where wrong checkpoints and overwritten output directories come from, and a prose plan does not expose them: it reads like intent, not like the values that will actually be used.

This skill renders those values, says where each one came from, and asks once.

## 1. Resolve what will actually be used

**Resolve by reading, never by running the thing you are about to confirm.** Executing the entry point to "see what it resolves to" is the launch you were asked to confirm: by the time the card appears, the money is spent. Read the files instead, and use a resolver only when it is explicitly a no-op (`--print-config`, `--cfg job --resolve`, `--dryrun`, `--test-only`); check `--help` first if you are unsure whether a flag trains.

Work out the settings the pending command will really see, in this order of authority: explicit command-line arguments, then the config files that command loads (follow includes and inheritance), then environment variables, then framework defaults. If the project ships a resolver, use it instead of guessing: `python train.py --cfg job --resolve` for Hydra, `accelerate env`, `python -c "import json,yaml;..."` for a plain YAML, or the project's own `--print-config` flag. Resolve interpolations: show `llama3-8b-s1337`, never `${model}-s${seed}`.

Tag every value with where it came from. The tag matters as much as the value:

| Tag | Means |
|---|---|
| `YOU SAID` | the user stated it in this session; quote their words |
| `INFERRED` | the agent worked it out; name the evidence (`configs/base.yaml:12`, "same as the run you approved on Oct 1") |
| `DEFAULT` | a framework or config default nobody chose |
| `CARRIED` | unchanged from the last confirmed card |
| `UNKNOWN` | could not be resolved |

**`UNKNOWN` is not a failure to hide.** A setting you could not resolve is the most dangerous row on the card, because it is exactly the one nobody has checked. Never print a plausible default in its place. See `references/resolve.md` for how to resolve each common framework and what to do when a value only exists at runtime.

## 2. Diff against the last confirmed run

Read `.runcard/` for the most recent confirmed card of the same run family. Show the rows that changed (`~`), are newly set (`+`), are flagged (`!`) or are unknown (`?`); collapse the rest into one line: `19 settings identical to clip-1.0 (Oct 1)`. On a first run there is no baseline, so show the Tier-1 settings in full: data, model/checkpoint, output path, the three or four hyperparameters that define the run, hardware, and seed.

This diff is what keeps the card cheap to read and cheap in tokens. A full dump every time trains the user to skim.

## 3. Check across fields, not field by field

These five run every time, because each one is legal per field and wrong in combination. Do them before rendering, not after:

1. **Output collision** — does the output dir exist and already hold results?
2. **Checkpoint ↔ data** — when the card has both, **open the metadata files** (`config.json`, `tokenizer_config.json`, the yaml/json beside the weights, the dataset's tokenizer) and compare `vocab_size`, sequence length, image size, `num_labels`. This is a two-file read and the most expensive thing to discover an hour into training.
3. **Contradicted defaults** — any `DEFAULT` or `CARRIED` row that goes against something the user said earlier or in a previous card.
4. **Paths** — every path in the card: does it exist?
5. **Seed and precision** — seed reused while the config changed; precision the hardware cannot do.

`references/risks.md` has the rest (memory plausibility, irreversible side effects, tracker mismatch), how to word a flag, and how to estimate cost. Add one line of cost: runtime, the local clock time it would finish, and money if the hardware is billed; take the estimate from the ledger's own history when it exists and say `runtime unknown` when it does not.

## 4. Render one card, then ask once

Keep it to one screen. Quiet rows stay quiet; only flagged rows get emphasis, so the card looks different every time and does not become something the user clicks through. Then ask with a single structured question: **Launch** · **Fix a field** · **Show the full table** · **Abort**. Do not re-ask what the card already answers, and do not turn this into an interview; the card is the question.

## 5. Bind the answer, then launch

When the user confirms, write the exact command text they approved as one line in `.runcard/.confirmed`, then run it unchanged. The hook consumes that line, so one confirmation buys one launch, and any edit to the command afterwards is blocked again — that is the staleness check, enforced rather than promised. Immediately before executing, resolve once more: if a config file changed under you, the confirmation is void and only the delta goes back to step 4.

After launching, append the confirmed card to `.runcard/<run-name>.md` with the exact command, the provenance table, the timestamp and the resulting job id. Mask anything that looks like a credential. See `references/ledger.md`: this file is the diff baseline for the next run, a record of what was actually run, and usable material for a paper's methods section.

## Gotchas

- **Running the trainer to resolve the config is the mistake this skill exists to prevent.** It happened in our own benchmark: a perfect card was rendered *after* the entry point had already been executed. If no safe resolver exists, read the files and mark what you cannot resolve `UNKNOWN`.
- **The config the agent reads is not always the config the job reads.** Cluster jobs often re-resolve on the compute node with a different working directory or environment; say so when the command is `sbatch`/`srun`, and prefer the resolver the job itself would run.
- **A value that only exists at runtime cannot be confirmed.** Auto batch size, `device_map="auto"`, dynamic LR schedules: mark these as runtime-resolved rather than pretending to a number.
- **The expensive mistake is usually the quiet one.** The dangerous row is rarely the learning rate the user typed; it is the output path or the checkpoint nobody mentioned.
- **A hook that blocks work gets uninstalled.** If anything in the interception path fails, fail open with a visible note.
- **Don't re-ask what was already settled.** If the user has confirmed this exact configuration, launch; re-confirmation is only for what changed.
- **Masking is not optional.** Tokens and keys reach the card through environment variables; a card is a file that gets committed.

## When not to use this

- Cheap, reversible commands: a test run, a linter, a one-second script. Interception there is noise, and noise is how this skill gets turned off.
- The user explicitly asked to run something right now and has already seen the settings this session: say what changed, or launch.
- Choosing what the experiment should be: that is a planning or grilling skill. This one only shows what is about to happen.
