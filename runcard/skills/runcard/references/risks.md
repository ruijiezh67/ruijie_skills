# Cross-field risk checks

Each of these settings is legal on its own. The damage comes from the combination, which is why per-field validation misses them. Run the cheap checks always; run the ones that need file reads when the fields involved are present.

| # | Check | How to check cheaply | Flag reads |
|---|---|---|---|
| 1 | **Output collision** | does the output dir / run name already exist, and does it contain checkpoints, logs or results? | `! output: runs/clip-1.0/ exists with 4 files (last written Oct 1) — this run would write into it` |
| 2 | **Checkpoint ↔ data mismatch** | whenever the card has both a checkpoint and a dataset, **open the metadata beside each**: `config.json`, `tokenizer_config.json`, `generation_config.json`, `preprocessor_config.json`, or the `*.yaml`/`*.json` written next to the weights, and the dataset's own card or tokenizer. Compare `vocab_size`, `max_position_embeddings` vs `model_max_length`, image size, `num_labels`, task head. Two files is a cheap read and this is the most expensive failure to discover after an hour of training | `! ckpt vocab 32000 vs tokenizer 32768 — size mismatch at load` |
| 3 | **Seed reuse with a changed config** | same seed as the last confirmed card, but other fields changed | `! seed 1337 reused while lr and data changed — runs are not comparable, and the name suggests they are` |
| 4 | **Precision vs hardware** | bf16 on pre-Ampere, fp8 off Hopper, fp16 on CPU | `! bf16 requested; detected GPU is a T4 (no bf16)` |
| 5 | **Missing paths** | every path in the resolved settings: does it exist and is it readable? | `! data/v3_qc.jsonl does not exist (data/v3.jsonl does)` |
| 6 | **Memory plausibility** | batch × seq × params heuristic against device memory, or simply: this exact combination OOM'd before (see the ledger) | `! batch 64 at seq 4096 OOM'd on this GPU on Sep 28` |
| 7 | **Silently inherited values** | any `DEFAULT` or `CARRIED` row that contradicts something the user said earlier in the session | `! num_workers 0 (default) — you asked for 8 on Sep 30` |
| 8 | **Scale of the spend** | runtime × rate; also wall-clock finish time | `≈ 2h10m on 1×A100 ≈ $4.60 · finishes 03:40 local` |
| 9 | **Irreversibility** | does it push, publish, delete, or overwrite anything outside the output dir? | `! will push to origin/main` |
| 10 | **Tracker mismatch** | project/entity/run-name differ from the family's previous runs | `! wandb project "scratch" — previous runs went to "fig3-revision"` |

## How to flag

- `!` for a risk that could waste the run or destroy data. Give the evidence in the same line; a flag without evidence is noise.
- `?` for `UNKNOWN`, which is a risk of a different kind: nobody has checked it.
- Never flag more than a handful. If everything is loud, nothing is. Rank by what would cost the most to discover after the run.
- A flagged row does not block. The user can waive it; record the waiver in the ledger entry so the next card does not re-litigate it.

## Cost estimates

Be explicit about where the estimate comes from: the ledger's own history for this family ("last run of this config took 1h55m"), the scheduler's estimate, or a stated rate per hour. If none of those exist, say `runtime unknown` rather than inventing a number. The user's rule applies here too: unmeasured is not zero.
