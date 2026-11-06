import csv, sys
from collections import Counter

rows = list(csv.DictReader(open(sys.argv[1])))
y = [int(r["y_true"]) for r in rows]
p = [int(r["y_pred"]) for r in rows]
right = sum(a == b for a, b in zip(y, p))
f1s = []
for c in sorted(set(y)):
    tp = sum(a == c and b == c for a, b in zip(y, p))
    fp = sum(a != c and b == c for a, b in zip(y, p))
    fn = sum(a == c and b != c for a, b in zip(y, p))
    f1s.append(2 * tp / (2 * tp + fp + fn) if tp else 0.0)
print(f"accuracy {right / len(y):.4f} ({right}/{len(y)})")
print(f"macro_f1 {sum(f1s) / len(f1s):.4f}")
