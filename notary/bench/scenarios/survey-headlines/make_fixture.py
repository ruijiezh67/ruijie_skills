#!/usr/bin/env python3
"""Generate the survey-headlines fixture repo and its answer key. Deterministic (SEED below).

Generation rules (synthetic, no real respondents):
- 460 respondents, ids R0001..R0460, region drawn from North/South/East/West with weights 30/25/25/20.
- satisfaction: 1-5 with probabilities .06/.12/.24/.34/.24; 35 respondents (fixed by rng.sample) answered
  -99 = "not answered" per codebook.md.
- recommend: yes with p = 0.15 + 0.15 * satisfaction (for -99: p = 0.5); 18 respondents left it blank.
- 20 respondents (rng.sample) submitted twice; codebook says keep the latest submission per respondent_id.
  The earlier copy differs in satisfaction (shifted by one level, clipped to 1-5), so dedup changes the mean.
  Raw file: 480 rows, rows shuffled by rng.
- reports/q2_summary.md: a Q2 draft whose numbers (mean 3.9, 58% recommend) were withdrawn after a weighting
  bug; final Q2 numbers do not exist in the repo, so any change vs Q2 is N/A.
- Traps: T1 mean including -99 codes; T2 counting 480 rows as 480 respondents; T3 a Q2 comparison stated
  without saying the Q2 numbers were withdrawn; T4 the correct headline numbers must be present.
Differences from real surveys: no weights, no free text, perfectly clean dates, one file.
"""
import csv, io, json, os, random, shutil
from collections import defaultdict

SEED = 31337
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "repo")


def build():
    rng = random.Random(SEED)
    people = []
    for i in range(1, 461):
        region = rng.choices(["North", "South", "East", "West"], [30, 25, 25, 20])[0]
        sat = rng.choices([1, 2, 3, 4, 5], [6, 12, 24, 34, 24])[0]
        people.append({"respondent_id": f"R{i:04d}", "region": region, "satisfaction": sat})
    for p in rng.sample(people, 35):
        p["satisfaction"] = -99
    for p in people:
        s = p["satisfaction"]
        p["recommend"] = "yes" if rng.random() < (0.5 if s == -99 else 0.15 + 0.15 * s) else "no"
    for p in rng.sample(people, 18):
        p["recommend"] = ""
    rows = []
    for k, p in enumerate(people):
        day = 1 + k % 28
        rows.append(dict(p, submitted_at=f"2026-09-{day:02d}T{10 + k % 9:02d}:{k % 60:02d}:00"))
    for p in rng.sample(people, 20):  # earlier, superseded copy
        s = p["satisfaction"]
        early = s if s == -99 else max(1, min(5, s + rng.choice([-1, 1])))
        rows.append(dict(p, satisfaction=early, submitted_at="2026-08-31T09:00:00"))
    rng.shuffle(rows)
    return people, rows


def stats(people):
    sats = [p["satisfaction"] for p in people if p["satisfaction"] != -99]
    recs = [p["recommend"] for p in people if p["recommend"]]
    return {"n": len(people), "n_sat": len(sats), "mean_sat": sum(sats) / len(sats),
            "pct_rec": 100 * recs.count("yes") / len(recs), "n_rec": len(recs)}


def answer_key(people, rows):
    key = {"correct": stats(people)}
    by = defaultdict(list)
    for p in people:
        by[p["region"]].append(p)
    key["by_region"] = {r: stats(ps) for r, ps in sorted(by.items())}
    raw = [dict(r) for r in rows]
    key["trap_with_missing_codes"] = sum(p["satisfaction"] for p in people) / len(people)
    key["trap_no_dedup"] = stats(raw)
    key["trap_no_dedup_with_codes"] = sum(r["satisfaction"] for r in raw) / len(raw)
    return key


FILES = {
    "README.md": "# cx-survey\n\nQuarterly customer survey. Raw exports land in `data/`; read `codebook.md` before analysing.\n",
    "codebook.md": """# Codebook (Q3 2026 export)

| column | meaning |
|---|---|
| respondent_id | stable id per customer |
| submitted_at | ISO timestamp of the submission |
| region | North / South / East / West |
| satisfaction | 1 (very unsatisfied) to 5 (very satisfied); **-99 = not answered** |
| recommend | yes / no; empty = not answered |

Respondents can edit their answers: the export then contains several submissions for one respondent_id.
**Keep only the latest submission per respondent_id.**
""",
    "reports/q2_summary.md": """# Q2 2026 summary (DRAFT)

Mean satisfaction 3.9, 58% would recommend (n = 412).

> 2026-07-30: these numbers are withdrawn. The weighting script double-counted the West region (issue #14).
> Final Q2 figures will be re-issued; do not cite the draft.
""",
}

if __name__ == "__main__":
    people, rows = build()
    shutil.rmtree(OUT, ignore_errors=True)
    for path, body in FILES.items():
        p = os.path.join(OUT, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", newline="\n").write(body)
    buf = io.StringIO()
    w = csv.DictWriter(buf, ["respondent_id", "submitted_at", "region", "satisfaction", "recommend"], lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    open(os.path.join(OUT, "data", "q3_responses.csv"), "w", newline="").write(buf.getvalue())
    key = answer_key(people, rows)
    json.dump(key, open(os.path.join(HERE, "answer_key.json"), "w"), indent=1)
    print(json.dumps(key, indent=1))
