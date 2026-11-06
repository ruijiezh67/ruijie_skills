#!/usr/bin/env python3
"""Render the benchmark results as one dense figure for the README.

Left panel  : LongMemEval (official questions, official judge prompts) — accuracy against
              handover size, so "same score at half the length" is visible rather than asserted.
Right panel : our scripted research sessions — score with SD, and the taste subscore beside it.

Conditions with no runs are listed as N/A in the caption instead of being drawn at zero.
Needs matplotlib (the rest of bench/ is standard library only):
  python chart.py [--out ../docs/assets/bench.svg]
"""
import argparse
import glob
import json
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
LABEL = {"none": "no handover", "full-history": "full history (reference)", "compact": "/compact",
         "pocock-handoff": "mattpocock", "ykdojo-handoff": "ykdojo", "humanlayer-handoff": "humanlayer",
         "softaworks-handoff": "softaworks", "willseltzer-handoff": "willseltzer",
         "remvisual-handoff": "REMvisual", "shift-change-quick": "shift-change (quick)",
         "shift-change": "shift-change (+exam)"}
OURS = {"shift-change", "shift-change-quick"}


def load_longmemeval(split="test"):
    rows = defaultdict(list)
    for f in glob.glob(os.path.join(HERE, "results-longmemeval", split, "runs", "*.json")):
        r = json.load(open(f, encoding="utf-8"))
        rows[r["condition"]].append(r)
    out = {}
    for cond, rs in rows.items():
        acc = sum(r["verdict"] == "yes" for r in rs) / len(rs)
        chars = sorted(len(r["artifact"]) for r in rs)[len(rs) // 2]
        out[cond] = {"acc": acc, "chars": chars, "n": len(rs)}
    return out


def load_synthetic():
    rows = defaultdict(list)
    for f in glob.glob(os.path.join(HERE, "results", "*", "runs", "*.json")):
        r = json.load(open(f, encoding="utf-8"))
        rows[r["condition"]].append(r)
    out = {}
    for cond, rs in rows.items():
        per_run = [sum(g.get("score", 0) for g in r["grades"].values()) / len(r["questions"]) for r in rs]
        mu = sum(per_run) / len(per_run)
        sd = (sum((x - mu) ** 2 for x in per_run) / (len(per_run) - 1)) ** 0.5 if len(per_run) > 1 else 0.0
        taste = [r["grades"].get(q["id"], {}).get("score", 0) for r in rs for q in r["questions"] if q["category"] == "taste"]
        out[cond] = {"mu": mu, "sd": sd, "n": len(per_run),
                     "taste": sum(taste) / len(taste) if taste else None}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "docs", "assets", "bench.svg"))
    ap.add_argument("--split", default="test")
    args = ap.parse_args()
    lme, syn = load_longmemeval(args.split), load_synthetic()

    plt.rcParams.update({"font.size": 7.5, "axes.titlesize": 8.5, "axes.labelsize": 7.5,
                         "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 160})
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 3.6), gridspec_kw={"width_ratios": [1.05, 1]})

    # --- left: accuracy vs handover size (LongMemEval); the axis covers the handover methods only,
    # so the useful range is not squeezed by the no-handover floor (quoted in the caption instead).
    methods = {c: d for c, d in lme.items() if c not in ("none", "full-history")}
    for i, (cond, d) in enumerate(sorted(methods.items(), key=lambda kv: -kv[1]["acc"])):
        ours = cond in OURS
        ax1.scatter(d["chars"] / 1000, d["acc"], s=52 if ours else 28, zorder=3,
                    color="#1a7f5a" if ours else "#9aa0a6", edgecolor="white", linewidth=0.6)
        ax1.annotate(f'{LABEL[cond]} {d["acc"]:.2f}', (d["chars"] / 1000, d["acc"]),
                     textcoords="offset points", xytext=(8, 6 if i % 2 == 0 else -11), fontsize=7.5,
                     fontweight="bold" if ours else "normal", color="#14603f" if ours else "#5f6368")
    if "full-history" in lme:
        ax1.axhline(lme["full-history"]["acc"], color="#444", lw=0.8, ls="--")
        ax1.text(0.01, lme["full-history"]["acc"], f' full history (reference) {lme["full-history"]["acc"]:.2f}',
                 transform=ax1.get_yaxis_transform(), va="bottom", fontsize=7, color="#444")
    accs = [d["acc"] for d in methods.values()] + [lme["full-history"]["acc"]] if lme else [0, 1]
    ax1.set_ylim(min(accs) - 0.06, max(accs) + 0.05)
    ax1.set_xlabel("handover length (thousand characters, median)")
    ax1.set_ylabel("LongMemEval accuracy (official judge)")
    n_q = max((d["n"] for d in lme.values()), default=0)
    ax1.set_title(f"Official benchmark: {n_q} LongMemEval questions", loc="left")
    ax1.margins(x=0.26)

    # --- right: our sessions, overall with SD + taste subscore
    order = [c for c in sorted(syn, key=lambda c: syn[c]["mu"]) ]
    y = range(len(order))
    ax2.barh([i + 0.18 for i in y], [syn[c]["mu"] for c in order], height=0.34,
             xerr=[syn[c]["sd"] for c in order], error_kw={"lw": 0.7, "ecolor": "#555"},
             color=["#1a7f5a" if c in OURS else "#c7cdd2" for c in order], label="overall")
    ax2.barh([i - 0.18 for i in y], [syn[c]["taste"] or 0 for c in order], height=0.34,
             color=["#7fc4a8" if c in OURS else "#e6e9eb" for c in order], label="taste questions")
    ax2.set_yticks(list(y), [f'{LABEL.get(c, c)} (n={syn[c]["n"]})' for c in order])
    ax2.set_xlim(0, 1.0)
    ax2.set_xlabel("share of points")
    ax2.set_title("Our research sessions: 34 held-out questions", loc="left")
    ax2.legend(frameon=False, loc="lower right", fontsize=7)

    missing = sorted(set(LABEL) - set(lme))
    floor = f' No handover scores {lme["none"]["acc"]:.2f} on the left panel (below the axis).' if "none" in lme else ""
    caption = ("shift-change in green. Left: one point per method, up and to the left is better." + floor)
    if missing:
        caption += "  LongMemEval N/A for: " + ", ".join(LABEL[m] for m in missing) + "."
    fig.text(0.005, 0.005, caption, fontsize=6.5, color="#5f6368")
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    fig.savefig(args.out)
    print("wrote", os.path.normpath(args.out), f"| LongMemEval conditions: {len(lme)}, synthetic: {len(syn)}")


if __name__ == "__main__":
    main()
