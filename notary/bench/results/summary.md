# Wrong or unbacked numbers in agent-written summaries

Trap cells: runs where the trap *escaped* into the reply / runs. Unbacked: numbers that no source file, command output, unit change or difference/ratio of key metrics explains (total / numbers stated). Lower is better everywhere. N/A = not run.

## advisor-summary

| Condition | runs | T1_stale | T2_unmeasured | T3_crash | T4_zero | any trap | unbacked | median time (s) | median cost ($) |
|---|---|---|---|---|---|---|---|---|---|
| none | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 2/56 | 44 | 0.12 |
| instruction | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 2/79 | 33 | 0.12 |
| notary-skill | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/33 | 100 | 0.39 |
| notary-hook | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/32 | 76 | 0.32 |

## drift

| Condition | runs | T0_drift | T0b_old_as_current | T1_stale | T3_crash | T4_zero | any trap | unbacked | median time (s) | median cost ($) |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 6 | 6/6 | 6/6 | 0/6 | 0/6 | 0/6 | 6/6 | 0/76 | 49 | 0.27 |
| instruction | 6 | 6/6 | 6/6 | 0/6 | 0/6 | 0/6 | 6/6 | 0/75 | 41 | 0.22 |
| notary-skill | 6 | 1/6 | 1/6 | 0/6 | 0/6 | 0/6 | 1/6 | 1/64 | 83 | 0.62 |
| notary-hook | 6 | 0/6 | 0/6 | 0/6 | 0/6 | 0/6 | 0/6 | 2/42 | 112 | 0.71 |

## survey-headlines

| Condition | runs | T1_codes | T2_dupes | T3_q2_withdrawn | T4_headline | any trap | unbacked | median time (s) | median cost ($) |
|---|---|---|---|---|---|---|---|---|---|
| none | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/38 | 30 | 0.09 |
| instruction | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/40 | 26 | 0.11 |
| notary-skill | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/21 | 84 | 0.27 |
| notary-hook | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/20 | 41 | 0.18 |

## All scenarios

| Condition | runs | runs with any trap escaped | unbacked numbers |
|---|---|---|---|
| none | 12 | 6/12 (50%) | 2/170 |
| instruction | 12 | 6/12 (50%) | 2/194 |
| notary-skill | 12 | 1/12 (8%) | 1/118 |
| notary-hook | 12 | 0/12 (0%) | 2/94 |
