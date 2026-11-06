# Resolving settings, per framework

The goal is the values the command will actually see, not the values written in the file you happened to open. Prefer a resolver the project already has; fall back to reading; mark what neither can give you.

## Order of authority

1. Explicit command-line arguments (including `--key=value`, `key=value` Hydra overrides, `-c` config paths).
2. Config files that the command loads, following includes, `defaults:` lists and inheritance.
3. Environment variables the code reads (`os.environ`, `${oc.env:...}`, `.env` files loaded by the entry point).
4. Framework or code defaults (`argparse` defaults, dataclass fields, library defaults).

Later sources lose to earlier ones. When two sources disagree, say which one wins in the card.

## Per framework

| Stack | Resolver to run | Falls short when |
|---|---|---|
| Hydra | `python <entry>.py --cfg job --resolve` (add the same overrides the real command has) | a resolver needs a cluster-only env var: run it and keep `MISSING`/errors visible rather than filling in |
| argparse / click | parse the entry point: read `add_argument` defaults, then apply the command's flags | `nargs`, `type=` coercion and post-parse mutation; verify against the code path that uses the value |
| plain YAML/JSON/TOML | load with the stdlib, apply include/merge logic the code uses | values the code overrides after loading |
| accelerate / deepspeed | `accelerate env`, and read the `--config_file` yaml; for deepspeed also the json | the launcher may change world size at runtime |
| Slurm (`sbatch`, `srun`) | read the script's `#SBATCH` lines plus the command inside it; `sbatch --test-only` reports feasibility and an estimated start without submitting | the job re-resolves on the compute node, with a different cwd, modules and env |
| W&B sweeps | the sweep yaml plus the agent's overrides | per-trial values are drawn at runtime: mark them as a range, not a value |
| Cloud runners (modal, sky, runpod) | the project's spec file plus the CLI flags; `sky launch --dryrun` where available | instance type may be chosen at scheduling time |

## Settings worth resolving (Tier 1 on a first run)

Data (path, split, version/hash), model or checkpoint (path and step), output directory and run name, the handful of hyperparameters that define this run, hardware (device, count, precision), seed, and the tracker project/entity if one is used. Everything else belongs in the collapsed "identical" line or the full table.

## When a value cannot be resolved

Mark it `UNKNOWN` and say what would resolve it:

```
| lr_schedule | UNKNOWN | ? | built inside train.py:88 from `--lr` and `--max_steps`; run `python train.py --print-config` to see it |
```

Three specific cases:
- **Runtime-resolved** (auto batch size, `device_map="auto"`, dynamic schedules): write `runtime` with the rule that will decide it. Confirming a number nobody will use is worse than saying it is dynamic.
- **Cluster-only** (env modules, node-local paths): resolve what you can locally, and say the job re-resolves on the node.
- **Missing required** (Hydra `???`): this is a hard stop, not a flag. The job would fail; say so instead of launching.
