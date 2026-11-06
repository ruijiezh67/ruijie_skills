# Evaluations

Two things are measured, and they are different: whether the card **appears** when it should (triggering, below) and whether it **catches what matters** (output cases, below, and the benchmark in `../bench/`).

Run with `claude plugin eval` on a CLI that has the subcommand (`claude plugin --help`); `claude plugin eval init` generates the case files in the format your version expects. Otherwise run each prompt in a fresh session and check the expectation by hand.

## Triggering

The hook is pattern matching, so it is tested directly (see `../bench/test_hook.sh`); these cases test the skill's own description and the hook end to end.

| # | Prompt / command | Must happen |
|---|---|---|
| T1 | "run the grad_clip=1.5 experiment" in a project with a train script | a run card appears before anything executes |
| T2 | "submit the sweep to the cluster" | a run card appears; the `sbatch` command does not run first |
| T3 | "show me the run card" | the card is rendered on request, with no launch |
| T4 | `python analyse_results.py` | **no** card: reading results is not a costly run |
| T5 | `sbatch --test-only script.sbatch` | **no** card: a feasibility check is not a launch |
| T6 | `pytest tests/` | **no** card |
| T7 | the user already confirmed this exact configuration this session | it says so and launches, instead of re-asking |

## Output cases

| # | Setup | Expectation |
|---|---|---|
| O1 | config default contradicts something the user said in an earlier card | flagged, quoting the user's own words |
| O2 | output directory already holds a finished run | flagged as a collision before launch |
| O3 | checkpoint `config.json` vocab ≠ tokenizer vocab | flagged, with both numbers, having actually opened both files |
| O4 | a setting that cannot be resolved (built at runtime inside the script) | shown as `UNKNOWN`, never as a default value |
| O5 | the agent edits a config after the user confirms | the confirmation is void; only the delta is re-shown |
| O6 | launch confirmed | `.runcard/<run-name>.md` written, credentials masked, job id recorded |
| O7 | no previous card exists | Tier-1 settings shown in full rather than a diff against nothing |

Each regression found in real use gets a case here and an entry in `../CHANGELOG.md`.
