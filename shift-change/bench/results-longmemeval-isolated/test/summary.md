# LongMemEval handover results

Accuracy = share of questions judged correct by the official LongMemEval judge prompt (run on Claude). One run per question and condition.

| Condition | questions | Accuracy | single-session-user | single-session-assistant | single-session-preference | multi-session | knowledge-update | temporal-reasoning | abstention | Handover chars (median) | Handover time (s, median) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 21 | 0.24 | 0.00 | 0.67 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 0 | 0 |
| full-history | 21 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 | 0 |
| compact | 21 | 0.95 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 6559 | 31 |
| pocock-handoff | 21 | 0.76 | 0.67 | 0.67 | 0.33 | 0.67 | 1.00 | 1.00 | 1.00 | 5120 | 70 |
| remvisual-handoff | 21 | 0.95 | 1.00 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | 1.00 | 21857 | 120 |
| shift-change-quick | 21 | 0.95 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 8655 | 71 |
| shift-change | 21 | 0.95 | 1.00 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | 1.00 | 9708 | 102 |

51 runs failed for infrastructure reasons and were re-run; kept in `failed/`.
