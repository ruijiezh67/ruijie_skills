# Building the bundle

## Tracing dependencies

Start from what the receiver will run, and walk outward:

1. **Entry points**: the script, notebook or command the task centres on.
2. **Imports**: local modules they import (`import x`, `from x import`, `source()`, `library()` of local packages). Include local ones; third-party ones go into the environment section as pinned versions (`pip freeze | grep`, `conda env export --from-history`, `sessionInfo()`).
3. **Loaded files**: grep the entry points and their local imports for file access: `open(`, `read_csv`, `load`, `np.load`, `torch.load`, `readRDS`, `fread`, `yaml.safe_load`, `json.load`, `Path(`, string literals ending in data extensions (`.csv .jsonl .parquet .h5 .pt .ckpt .rds .yaml .json`).
4. **Configs and environment**: config files, `.env` (never include the real one), Makefile/justfile targets, Slurm scripts, `module load` lines.
5. **What this session touched**: files read or edited while working on this part of the task. They often reveal a dependency that code-reading misses (a notes file, a hand-edited CSV).
6. **Reference outputs**: expected results, baseline numbers or figures the receiver must match or beat.

For each file decide include / link / regenerate / manifest-only. Rules of thumb: include text files under ~1 MB that the task needs; manifest-only for data over ~50 MB or anything with licensing or privacy limits; regenerate anything a single command rebuilds in minutes.

Checksums: `python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" FILE` (use `sha256sum` where available).

## MANIFEST.md

```markdown
# Manifest
| Path (repo-relative) | Class | Size | sha256 (first 12) | How to get it |
|---|---|---|---|---|
| src/train.py | include | 4 KB | 3f2a… | files/src/train.py |
| data/v3_dedup.jsonl | manifest-only | 212 MB | 9c1e… | shared drive: /lab/data/v3_dedup.jsonl |
| runs/baseline/metrics.json | regenerate | – | – | `python eval.py --ckpt baseline` |
| github.com/org/lib | link | – | commit 1a2b3c | `pip install git+…@1a2b3c` |
```

## BRIEF.md

```markdown
# Brief: <task title>
From <sender> to <receiver> · <date> · deadline <date, if any>

## Goal
<2–4 sentences: what to achieve and why it matters for the larger project>

## Context you need
<the minimum background: what the project is, what has been done, where this piece fits>

## What's already done
- <item> [verified: <command> → <result>]

## Your task
1. <step, with the files involved>

## No-go zones
| Don't | Why | Unless |
|---|---|---|

## Conventions
- <how the sender wants things done: code style, tools, what not to touch, how to report back>

## Acceptance criteria
| Check | Command | Expected |
|---|---|---|
| <eval runs on dev> | `python eval.py --split dev` | prints `acc >= 0.70` |

## Open questions
- <things the sender doesn't know either; say so rather than letting the receiver assume>

## How to report back
<PR / message / file to drop where, and what to include>
```

## START_HERE.md

```markdown
# Start here
1. Setup: <environment steps, exact commands>
2. Get the data: see MANIFEST.md rows marked manifest-only.
3. Sanity check: `<one quick command>` should print `<expected>`.

## Paste this into your AI agent
> You are picking up a delegated task. Read BRIEF.md and MANIFEST.md in this folder first.
> Verify the setup steps in START_HERE.md work. Before changing anything, tell me in a few
> lines what you think the task is, the no-go zones, and your plan, and wait for my OK.
> When done, run every command under "Acceptance criteria" in BRIEF.md and show me the output.
```
