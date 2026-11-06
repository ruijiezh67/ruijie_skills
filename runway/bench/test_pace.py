#!/usr/bin/env python3
"""Deterministic checks for snap.py and pace.py. No model, no network, no randomness.

Fixture generation rule: every sample follows the status line schema documented
at https://code.claude.com/docs/en/statusline ("rate_limits.five_hour" /
"seven_day", each {used_percentage 0-100, resets_at epoch seconds}). Times are
offsets from a fixed T0 = 1_800_000_000; used% values are chosen by hand to sit
on each side of the tier thresholds (70 / 90 for 5h, 95 for 7d, pace 1.15).
Unlike real data: perfectly linear burn, no gaps, no session switches.
Run: python runway/bench/test_pace.py
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "runway", "scripts")
T0 = 1_800_000_000
H = 3600


def sample(ts, p5, r5, p7, r7):
    return {"ts": ts, "five_hour": {"pct": p5, "resets_at": r5}, "seven_day": {"pct": p7, "resets_at": r7}}


def pace(samples, now):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "s.jsonl")
        with open(p, "w") as f:
            f.writelines(json.dumps(s) + "\n" for s in samples)
        out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "pace.py"), "--json", "--now", str(now), "--samples", p],
                             capture_output=True, text=True, check=True).stdout
    return json.loads(out)


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def green_fresh_window():
    s = [sample(T0, 10, T0 + 4 * H, 20, T0 + 4 * 24 * H), sample(T0 + H, 20, T0 + 4 * H, 22, T0 + 4 * 24 * H)]
    r = pace(s, T0 + H)
    assert r["tier"] == "GREEN", r
    assert r["five_hour"]["burn_pct_per_h"] == 10.0, r
    assert r["five_hour"]["hours_to_cap"] == 8.0, r


@case
def amber_at_70():
    s = [sample(T0, 60, T0 + 2 * H, 30, T0 + 4 * 24 * H), sample(T0 + H, 72, T0 + 2 * H, 32, T0 + 4 * 24 * H)]
    assert pace(s, T0 + H)["tier"] == "AMBER"


@case
def red_at_90():
    s = [sample(T0, 91, T0 + H, 30, T0 + 4 * 24 * H)]
    assert pace(s, T0)["tier"] == "RED"


@case
def red_when_cap_under_20_min():
    # 85% used, burning 60%/h -> 15% left = 15 min
    s = [sample(T0, 55, T0 + 2 * H, 30, T0 + 4 * 24 * H), sample(T0 + 1800, 85, T0 + 2 * H, 31, T0 + 4 * 24 * H)]
    assert pace(s, T0 + 1800)["tier"] == "RED"


@case
def weekly_ahead_of_pace_is_amber():
    # 1 day of 7 elapsed (resets in 6 days), 40% used -> pace 2.8x
    s = [sample(T0, 5, T0 + 4 * H, 40, T0 + 6 * 24 * H)]
    r = pace(s, T0)
    assert r["tier"] == "AMBER" and r["seven_day"]["pace_ratio"] > 1.15, r


@case
def weekly_underuse_near_reset_says_pull_forward():
    s = [sample(T0, 5, T0 + 4 * H, 30, T0 + 24 * H)]
    r = pace(s, T0)
    assert r["tier"] == "GREEN" and any("pull heavy work forward" in x for x in r["reasons"]), r


@case
def reset_since_last_sample_is_unknown_not_zero():
    s = [sample(T0, 95, T0 + H, 50, T0 + 4 * 24 * H)]
    r = pace(s, T0 + 2 * H)
    assert r["five_hour"]["pct"] is None and "unknown" in r["five_hour"]["note"], r
    assert r["tier"] != "GREEN" or r["seven_day"]["pct"] is not None, r


@case
def no_samples_is_unknown():
    assert pace([], T0)["tier"] == "UNKNOWN"


@case
def single_sample_has_no_burn_rate():
    r = pace([sample(T0, 10, T0 + 4 * H, 20, T0 + 4 * 24 * H)], T0)
    assert r["five_hour"]["burn_pct_per_h"] is None, r


@case
def snap_records_documented_schema():
    import time
    now = int(time.time())
    payload = {"model": {"display_name": "Opus"},
               "rate_limits": {"five_hour": {"used_percentage": 23.5, "resets_at": now + 3 * H},
                               "seven_day": {"used_percentage": 41.2, "resets_at": now + 3 * 24 * H}}}
    with tempfile.TemporaryDirectory() as d:
        env = dict(os.environ, RUNWAY_DIR=d)
        run = lambda p: subprocess.run([sys.executable, os.path.join(SCRIPTS, "snap.py")], input=json.dumps(p),
                                       capture_output=True, text=True, env=env, encoding="utf-8").stdout
        line = run(payload)
        run(payload)  # unchanged within 5 min: not written again
        rows = open(os.path.join(d, "samples.jsonl")).read().splitlines()
        assert len(rows) == 1 and json.loads(rows[0])["five_hour"]["pct"] == 23.5, rows
        assert "5h 24%" in line and "7d 41%" in line, line
        assert "no rate_limits" in run({"model": {}})  # API-key session: no crash, no sample
        assert len(open(os.path.join(d, "samples.jsonl")).read().splitlines()) == 1


if __name__ == "__main__":
    bad = 0
    for c in CASES:
        try:
            c()
            print("ok  ", c.__name__)
        except AssertionError as e:
            bad += 1
            print("FAIL", c.__name__, e)
    print(f"{len(CASES) - bad}/{len(CASES)} passed")
    sys.exit(1 if bad else 0)
