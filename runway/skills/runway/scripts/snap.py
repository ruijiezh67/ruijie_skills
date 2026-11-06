#!/usr/bin/env python3
"""Status line command: record Claude Code's rate-limit windows, print one short line.

Claude Code pipes session JSON to the status line on stdin. For Pro/Max
subscribers it carries rate_limits.five_hour / seven_day {used_percentage,
resets_at}. We append a sample to samples.jsonl when a value changes or 5
minutes pass, so pace.py can measure burn rate. Never raises: a broken status
line is worse than a missing sample.
"""
import json, os, sys, time

DIR = os.environ.get("RUNWAY_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "runway")
MIN_GAP = 300  # seconds between unchanged samples


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        print("runway: no input")
        return
    rl = data.get("rate_limits") or {}
    now = int(time.time())
    sample = {"ts": now}
    for w in ("five_hour", "seven_day"):
        win = rl.get(w) or {}
        if win.get("used_percentage") is not None:
            sample[w] = {"pct": win["used_percentage"], "resets_at": win.get("resets_at")}
    if len(sample) == 1:
        print("runway: no rate_limits yet")  # absent before first response, or not a subscriber
        return
    try:
        os.makedirs(DIR, exist_ok=True)
        last_path = os.path.join(DIR, "last.json")
        last = {}
        if os.path.exists(last_path):
            with open(last_path, encoding="utf-8") as f:
                last = json.load(f)
        same = {k: v for k, v in last.items() if k != "ts"} == {k: v for k, v in sample.items() if k != "ts"}
        if not same or now - last.get("ts", 0) >= MIN_GAP:
            with open(os.path.join(DIR, "samples.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(sample) + "\n")
            with open(last_path, "w", encoding="utf-8") as f:
                json.dump(sample, f)
    except Exception:
        pass
    parts = []
    for w, label in (("five_hour", "5h"), ("seven_day", "7d")):
        if w in sample:
            left = (sample[w]["resets_at"] or now) - now
            parts.append(f"{label} {sample[w]['pct']:.0f}% ↻{left // 3600}h{left % 3600 // 60:02d}m")
    print(" · ".join(parts))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows GBK/cp1252 consoles can't print ↻
    except AttributeError:
        pass
    main()
