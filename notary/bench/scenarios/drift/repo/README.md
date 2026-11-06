# topic-clf

Five-class topic classifier (DistilRoBERTa) for the lab's news corpus.

## Results (Sep 12)

| run | test acc | macro-F1 |
|---|---|---|
| baseline | 0.884 | 0.871 |
| aug | 0.913 | 0.902 |

## Layout
- `configs/` one YAML per run
- `runs/<name>/` metrics.json (validation), preds.csv (test predictions), train.log
- `eval_test.py runs/<name>/preds.csv` prints test accuracy and macro-F1
