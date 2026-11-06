# Codebook (Q3 2026 export)

| column | meaning |
|---|---|
| respondent_id | stable id per customer |
| submitted_at | ISO timestamp of the submission |
| region | North / South / East / West |
| satisfaction | 1 (very unsatisfied) to 5 (very satisfied); **-99 = not answered** |
| recommend | yes / no; empty = not answered |

Respondents can edit their answers: the export then contains several submissions for one respondent_id.
**Keep only the latest submission per respondent_id.**
