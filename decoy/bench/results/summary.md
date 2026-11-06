# Fake customer data: unsafe values, data card, reproducibility

Unsafe: values that could belong to a real person or host / values of that kind in the file. Card ok: a data card with generator, seed value, rules, standard, target and differences. Regen: re-running the agent's script recreates the identical file. N/A = not measured.

| Condition | runs (with CSV) | unsafe email | unsafe phone | unsafe card | unsafe ssn | unsafe ip | card ok | regen identical | median time (s) | median cost ($) |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 3 (3) | 0/600 | 0/600 | 600/600 | 0/600 | 0/600 | 0/3 | 3/3 | 40 | 0.13 |
| one-liner | 3 (3) | 0/600 | 0/600 | 0/600 | 0/600 | 0/600 | 0/3 | 3/3 | 48 | 0.17 |
| decoy-skill | 3 (3) | 0/600 | 0/600 | 0/600 | 0/600 | 0/600 | 3/3 | 3/3 | 51 | 0.18 |
