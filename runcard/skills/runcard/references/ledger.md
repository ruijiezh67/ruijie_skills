# The ledger: `.runcard/`

Every confirmed card is appended to `.runcard/<run-name>.md`. It serves three purposes at once, which is why it is worth the file: it is the baseline for the next diff, the record of what was actually run, and the raw material for a methods section.

## Card format

```markdown
# Run card: clip-1.5 · 2026-10-02 14:07 · confirmed by the user
Command:
`sbatch scripts/train.sbatch --config configs/clip.yaml grad_clip=1.5 seed=1337`
Job: slurm 481702 on greatlakes · est. 2h10m, finishes ~16:20 local

| Setting | Value | From | Note |
|---|---|---|---|
| data | data/v3_qc.jsonl (sha 9c1e…, 4,812 rows) | CARRIED | identical to clip-1.0 |
| checkpoint | runs/base/ckpt_12000.pt | YOU SAID | "start from the 12k checkpoint" |
| grad_clip | 1.5 | YOU SAID | — |
| lr | 3e-5 | DEFAULT | configs/clip.yaml:7, nobody chose it |
| precision | bf16 | INFERRED | A100 detected, matches clip-1.0 |
| output | runs/clip-1.5/ | INFERRED | run name from grad_clip |
| num_workers | UNKNOWN | ? | set inside train.sbatch from $SLURM_CPUS_PER_TASK |

Waived: `! seed 1337 reused while grad_clip changed` — user: "intentional, I want the same data order"
Settings hash: 7f3a9c21
```

Keep it to the settings that define the run. The point is a card someone can read in fifteen seconds next month, not a config dump; the full config already lives in the run directory.

## Rules

- **One file per run name.** A second run with the same name appends a new card with its timestamp; it does not overwrite. Two cards under one name is itself a useful signal that a run was repeated.
- **Mask credentials.** Any value matching a token/key/password pattern becomes `<masked>`; keep the variable name so the reader knows it was set. The ledger is a file that gets committed.
- **Record waivers.** A flagged risk the user waived, with their reason, so the next card does not raise it again from scratch.
- **Record the settings hash** that the confirmation was bound to, and the job id once it exists.
- **Do not write a card for a run that was not launched.** An aborted card is noise; the conversation already holds the reason.

## Using the ledger

- **Diff baseline**: the most recent card of the same family is what the next card compares against.
- **"What did we actually run?"**: the question that normally needs an archaeology session through old logs.
- **Methods section**: the cards for a figure's runs contain the data version, model, hyperparameters, hardware and seeds, already in one place.
- **`shift-change` handovers**: list `.runcard/` under required reading; the next session then has every confirmed configuration without the handover having to restate any of it.

Commit the ledger with the project unless the user prefers otherwise; it is evidence, not scratch. If they would rather keep it out of version control, add `.runcard/` to `.gitignore` and say so once.
