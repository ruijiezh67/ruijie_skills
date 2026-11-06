# LongMemEval handover results

Accuracy = share of questions judged correct by the official LongMemEval judge prompt (run on Claude). One run per question and condition.

| Condition | questions | Accuracy | single-session-user | single-session-assistant | single-session-preference | multi-session | knowledge-update | temporal-reasoning | abstention | Handover chars (median) | Handover time (s, median) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 21 | 0.19 | 0.00 | 0.33 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 0 | 0 |
| full-history | 21 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 | 0 |
| compact | 21 | 0.67 | 0.67 | 0.67 | 1.00 | 0.67 | 0.67 | 0.00 | 1.00 | 9400 | 86 |
| pocock-handoff | 21 | 0.76 | 0.67 | 0.67 | 1.00 | 1.00 | 0.33 | 0.67 | 1.00 | 6490 | 100 |
| remvisual-handoff | 21 | 0.71 | 0.67 | 1.00 | 0.67 | 0.67 | 0.33 | 0.67 | 1.00 | 18060 | 238 |
| shift-change-quick | 21 | 0.76 | 1.00 | 0.67 | 1.00 | 1.00 | 0.67 | 0.33 | 0.67 | 7425 | 115 |
| shift-change | 21 | 0.81 | 1.00 | 0.67 | 0.67 | 1.00 | 0.67 | 0.67 | 1.00 | 8952 | 228 |

1 runs failed for infrastructure reasons and were re-run; kept in `failed/`.
