#!/usr/bin/env python3
"""Read runway samples, report quota state, burn rate and a GREEN/AMBER/RED tier.

Usage: pace.py [--json] [--now EPOCH] [--samples PATH]

Unmeasured values are None (printed N/A), never 0: a window that has reset
since the last sample has an unknown used%, not a zero one.
"""
import argparse, json, os, time

DIR = os.environ.get("RUNWAY_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "runway")
WEEK = 7 * 24 * 3600
STALE = 15 * 60


def load(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def window(samples, key, now):
    """State of one window from the samples that share the latest resets_at."""
    rows = [s for s in samples if key in s]
    if not rows:
        return {"pct": None, "resets_at": None, "note": "no samples"}
    last = rows[-1]
    resets_at = last[key]["resets_at"]
    if resets_at and now >= resets_at:
        return {"pct": None, "resets_at": None, "note": "reset since last sample; used% unknown until next response"}
    same = [s for s in rows if s[key]["resets_at"] == resets_at]
    rate = None  # %/hour while in this window
    if len(same) >= 2 and same[-1]["ts"] - same[0]["ts"] >= 300:
        rate = (same[-1][key]["pct"] - same[0][key]["pct"]) / ((same[-1]["ts"] - same[0]["ts"]) / 3600)
    st = {
        "pct": last[key]["pct"],
        "resets_at": resets_at,
        "resets_in_h": round((resets_at - now) / 3600, 2) if resets_at else None,
        "burn_pct_per_h": round(rate, 2) if rate is not None else None,
        "sample_age_min": round((now - last["ts"]) / 60, 1),
        "note": "stale" if now - last["ts"] > STALE else "",
    }
    st["hours_to_cap"] = round((100 - st["pct"]) / rate, 2) if rate and rate > 0 else None
    return st


def tier(f, w):
    """Returns (tier, reasons). Unknown inputs never push toward GREEN on their own."""
    why = []
    if f["pct"] is None and w["pct"] is None:
        return "UNKNOWN", ["no current sample; send one message, then re-run"]
    if (f["pct"] or 0) >= 90 or (w["pct"] or 0) >= 95 or (f.get("hours_to_cap") is not None and f["hours_to_cap"] < 0.33):
        why.append("near a cap: wrap up, checkpoint, launch non-model jobs")
        return "RED", why
    if w["pct"] is not None and w["resets_in_h"] is not None:
        elapsed = 1 - w["resets_in_h"] * 3600 / WEEK
        pace = w["pct"] / max(elapsed * 100, 1)
        w["pace_ratio"] = round(pace, 2)
        if pace > 1.15 and w["pct"] >= 30:
            why.append(f"weekly use {pace:.2f}x ahead of even pace")
        elif w["resets_in_h"] < 48 and w["pct"] < 70:
            why.append(f"weekly reset in {w['resets_in_h']:.0f}h with {100 - w['pct']:.0f}% unused: pull heavy work forward")
    if (f["pct"] or 0) >= 70 or any("ahead" in r for r in why):
        return "AMBER", why + ["small, finishable tasks only"]
    return "GREEN", why + ["headroom for heavy tasks"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--now", type=int, default=None)
    ap.add_argument("--samples", default=os.path.join(DIR, "samples.jsonl"))
    a = ap.parse_args()
    now = a.now or int(time.time())
    s = load(a.samples)
    f, w = window(s, "five_hour", now), window(s, "seven_day", now)
    t, why = tier(f, w)
    res = {"tier": t, "reasons": why, "five_hour": f, "seven_day": w, "samples": len(s)}
    if a.json:
        print(json.dumps(res, indent=1))
        return
    na = lambda v, u="": "N/A" if v is None else f"{v}{u}"
    print(f"tier {t}: " + "; ".join(why))
    for k, st in (("5h", f), ("7d", w)):
        print(f"  {k}: used {na(st['pct'], '%')}, resets in {na(st.get('resets_in_h'), 'h')}, "
              f"burn {na(st.get('burn_pct_per_h'), '%/h')}, cap in {na(st.get('hours_to_cap'), 'h')} {st['note']}")


if __name__ == "__main__":
    main()
