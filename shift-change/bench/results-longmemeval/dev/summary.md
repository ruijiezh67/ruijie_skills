# LongMemEval handover results

Accuracy = share of questions judged correct by the official LongMemEval judge prompt (run on Claude). One run per question and condition.

| Condition | questions | Accuracy | single-session-user | single-session-assistant | single-session-preference | multi-session | knowledge-update | temporal-reasoning | abstention | Handover chars (median) | Handover time (s, median) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 21 | 0.14 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 0 | 0 |
| full-history | 21 | 0.95 | 1.00 | 1.00 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | 0 | 0 |
| shift-change-quick | 21 | 0.71 | 1.00 | 0.33 | 0.67 | 0.67 | 1.00 | 0.33 | 1.00 | 6371 | 120 |
