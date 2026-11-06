# runcard

**See what your agent is actually about to run.**

> **Status (2026-11-06): v0.1, headline does not hold on the current model.** The "Does it work?" table was measured on 2026-10-02. Re-run on 2026-10-27 with Claude Code 2.1.310 (Opus 5.5), the no-skill baseline no longer launched the wrong run (0/10), so the table no longer shows a benefit; a harder scenario is needed. See the [CHANGELOG](CHANGELOG.md). The raw scenario and results are kept out of this repo: they contain a non-English request.

Before a training run, a sweep, a cluster submission or any command that costs real time or money, `runcard` resolves every setting the command will truly use, says **where each one came from**, flags the combinations that are quietly wrong, and asks once.

<!-- demo: docs/assets/demo.gif -->

---

## The problem

You say "run it with grad_clip 1.5". The agent resolves forty settings and shows you one. The other thirty-nine come from a config default, from a previous run, or from a guess — and that is where the wrong checkpoint, the overwritten results directory and the dataset with duplicates come from. You find out ninety minutes later.

Asking more questions doesn't fix it either: a long Q&A costs tokens and attention, and agents are measurably bad at noticing what they should have asked. On [AMBIG-SWE](https://codex.danielvaughan.com/2026/04/13/ambig-swe-silent-guessing-problem-codex-cli/), agents that cannot ask resolve 37.9% of ambiguous tasks versus 59.5% when they can, and one model failed to notice missing information **100%** of the time. Agents guess silently. That is the behaviour to intercept.

## What a run card looks like

```
## Runcard: clip-1.5                    4 carried · 2 changed · 3 flagged

  !  data          data/v3.jsonl     DEFAULT configs/clip.yaml:1
                   ↳ you said "always the qc file, v3.jsonl has duplicates" (clip-1.0)
  !  num_workers   0                 DEFAULT configs/clip.yaml:7
                   ↳ you said "0 is painfully slow, use 8" (clip-1.0)
  !  checkpoint    ckpt/base         CARRIED
                   ↳ ckpt vocab_size 32000 vs tokenizer 32768 — size mismatch at load
  ~  grad_clip     1.5               YOU SAID        was 1.0
  ~  output        runs/clip-1.5     INFERRED        new dir, no collision
     5 settings identical to clip-1.0 (Sep 28)

  Cost: clip-1.0 took 1h55m on 1×A100. Runtime on this machine unknown.

  Launch · Fix a field · Show full table · Abort
```

Every row carries its provenance: **YOU SAID** (with your words), **INFERRED** (with the evidence), **DEFAULT**, **CARRIED** from the last confirmed run, or **UNKNOWN**. A setting that could not be resolved is shown as `UNKNOWN`, never as a plausible default — the unchecked value is the dangerous one.

## What it does

1. **Resolves** the settings the command will actually see: command line, config files it loads, environment, and the project's own resolver (`hydra --cfg job --resolve`, `accelerate env`) when one exists.
2. **Diffs** against the last confirmed card in `.runcard/`, so identical settings collapse to one line. The card costs what the *change* costs, not what the config costs.
3. **Checks across fields**, where the real damage lives: output collision, checkpoint↔dataset mismatch, defaults that contradict what you said earlier, missing paths, seed reused while the config changed, precision the hardware can't do.
4. **Asks once**: Launch · Fix a field · Show full table · Abort.
5. **Binds** your confirmation to a hash of the settings. If the agent changes anything between "yes" and launch, the confirmation is void and only the delta comes back.
6. **Records** the confirmed card in `.runcard/` — your diff baseline, your record of what was actually run, and the raw material for a methods section.

## Does it work?

One scenario so far (`bench/scenarios/clip-rerun`): a second run of a finished experiment, five traps planted in the project, one request that mentions none of them. The measurement is **deterministic** — the fixture's entry point records the settings it resolved, so "did a wrong setting reach execution?" is read from a file rather than judged by a model. Two runs per condition. **One scenario is not a benchmark yet**; more are being added in [`bench/`](bench/).

| Condition | Wrong settings that reached execution | Named the problem | Time |
|---|---|---|---|
| no skill | **100%** (10/10) | 0% | 24 s |
| runcard skill, **no hook** | **100%** (10/10) | 0% | 22 s |
| runcard skill **+ hook** | **0%** (0/10) | 80% | 90 s |

And with every condition told "if you would ask the user, stop and say what you would show them" — which is the only way plan mode and a question-asking skill can compete at all:

| Condition | Escaped | Named the problem | Stopped without saying why |
|---|---|---|---|
| plan mode | 0% | 0% | **100%** |
| grilling skill | 0% | 20% | 80% |
| runcard | 0% | **100%** | 0% |

Three things to take from this:

- **The skill alone is worth nothing here.** Without the hook it scored exactly like having no skill at all: an agent in a hurry to execute does not stop to consider a skill, however good the trigger phrases are. That is why the hook ships on by default, and it is why "just install the skill" is not offered as the recommended path.
- **Stopping is not the hard part; saying what is wrong is.** Plan mode and a grilling skill both halt, and both leave you no wiser.
- **The benchmark found three real bugs in this project**, including a hook that blocked nothing at all and a skill that resolved the config by running the trainer. They are written up in the [CHANGELOG](CHANGELOG.md).

## Install

**Claude Code plugin** (includes the hook, which is the part that matters)
```
/plugin marketplace add ruijiezh67/ruijie_skills
/plugin install runcard@ruijie-skills
```

**Skill only** (no interception; you invoke it)
```bash
git clone https://github.com/ruijiezh67/ruijie_skills
cp -r runcard/skills/runcard ~/.claude/skills/
```

## Usage

Normally you do nothing: the hook notices a costly command and the card appears. To ask for one directly:

```
show me the run card
what settings will this actually use?
```

The hook intercepts launchers (`torchrun`, `accelerate launch`, `deepspeed`, `sbatch`, `srun`, `wandb sweep`, `python *train*.py`, `nohup`, …) and spenders (`modal run`, `sky launch`, cloud batch, `docker run --gpus`), and deliberately ignores cheap or read-only commands (`--help`, `--dry-run`, `--test-only`, `pytest`, `squeue`, `nvidia-smi`). The patterns are a config block at the top of [`hooks/intercept.sh`](hooks/intercept.sh); extend them for your stack.

## FAQ

**How is this different from asking the agent to confirm?** A question gets you the three settings the agent thought to mention. The card gets you every setting that will be used, each tagged with where it came from, and the cross-field checks — and it costs one round trip, not a conversation.

**Isn't this just plan mode?** Plan mode describes intent in prose. This renders values, and binds the confirmation to them, so the plan cannot drift between approval and execution.

**Will it nag?** Only on commands that cost time or money, and only the changed and flagged rows. Routine rows stay quiet, which is deliberate: a warning you see every time is a warning you stop reading.

**Where do the cards go?** `.runcard/<run-name>.md`, committed by default because they are evidence. Add `.runcard/` to `.gitignore` if you would rather not.

## Philosophy

- The expensive mistake is the setting nobody mentioned.
- A value you could not resolve is `UNKNOWN`, not a default.
- Show the diff, not the config.
- A confirmation that isn't bound to the values isn't a confirmation.

## License

MIT
