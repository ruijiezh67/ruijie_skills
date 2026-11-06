#!/usr/bin/env python3
"""Mine a Claude Code session transcript for what a handover needs.

Compaction silently drops early turns from the live context, and those early
turns are where the user corrected the agent most. This script reads the raw
session file instead of the agent's memory and prints a markdown digest:
human messages (likely corrections flagged), tool denials with reasons,
interruptions, compaction points, files edited, and commands that may still
be running. Standard library only.

Usage:
  python mine_transcript.py                    # newest session for the current dir
  python mine_transcript.py --list             # recent sessions: id, span, prompts, opening line
  python mine_transcript.py --cwd /path/to/project
  python mine_transcript.py --session FILE.jsonl --max-chars 30000
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

CORRECTION = re.compile(
    r"(\bno\b|\bnope\b|don'?t|do not|instead|actually|wrong|\bstop\b|not what|i meant|i said|why did you|rather than|"
    r"prefer|always|never)",
    re.I,
)
NOISE = re.compile(
    r"<(system-reminder|ide_selection|ide_opened_file|local-command-stdout|local-command-stderr|local-command-caveat)>.*?</\1>",
    re.S,
)
BACKGROUND = re.compile(r"\b(sbatch|srun|qsub|bsub|nohup|tmux|screen|setsid|disown)\b|&\s*$")
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}


def list_sessions(cwd, limit=8):
    """Recent sessions for this directory, newest first: id, span, turns, and how it opened."""
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    want = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(cwd)).lower()
    files = [f for d in glob.glob(os.path.join(base, "projects", "*"))
             if os.path.basename(d).lower() == want for f in glob.glob(os.path.join(d, "*.jsonl"))]
    rows = []
    for path in sorted(files, key=os.path.getmtime, reverse=True)[:limit]:
        first = last = opener = None
        turns = 0
        for e in load(path):
            if e.get("type") != "user" or e.get("isMeta") or e.get("isCompactSummary"):
                continue
            if (e.get("origin") or {}).get("kind") not in (None, "human"):
                continue
            text = NOISE.sub("", text_of(e.get("message", {}).get("content", ""))).strip()
            if not text or text.startswith(("<command-name>", "<local-command", "Caveat:", "[Request interrupted")):
                continue
            turns += 1
            first = first or e.get("timestamp")
            last = e.get("timestamp")
            opener = opener or short(text, 90)
        rows.append((os.path.basename(path)[:-6], (first or "?")[:16], (last or "?")[11:16], turns, opener or "(no prompts)"))
    return rows


def find_session(cwd):
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    projects = os.path.join(base, "projects")
    want = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(cwd)).lower()
    dirs = [d for d in glob.glob(os.path.join(projects, "*")) if os.path.basename(d).lower() == want]
    files = [f for d in dirs for f in glob.glob(os.path.join(d, "*.jsonl"))]
    return max(files, key=os.path.getmtime) if files else None


def load(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def text_of(content):
    if isinstance(content, str):
        return content
    return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")


def short(s, n):
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def ts(entry):
    t = entry.get("timestamp") or ""
    return t[5:16].replace("T", " ") if len(t) >= 16 else "?"


def summarize_input(name, inp):
    if not isinstance(inp, dict):
        return ""
    for key in ("command", "file_path", "path", "pattern", "url", "description"):
        if key in inp:
            return short(str(inp[key]), 120)
    return short(", ".join(f"{k}={v}" for k, v in inp.items()), 120)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cwd", default=os.getcwd())
    ap.add_argument("--session", help="session id or path to a .jsonl (default: newest for --cwd)")
    ap.add_argument("--list", action="store_true", help="list recent sessions for --cwd and exit")
    ap.add_argument("--max-chars", type=int, default=20000)
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    if args.list:
        for sid, start, end, turns, opener in list_sessions(args.cwd):
            print(f"{sid}  {start.replace('T', ' ')}-{end}  {turns:3d} prompts  {opener}")
        return
    path = args.session or find_session(args.cwd)
    if path and not os.path.exists(path):  # --session took a bare session id
        base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
        hits = glob.glob(os.path.join(base, "projects", "*", f"{path}.jsonl"))
        path = hits[0] if hits else path
    if not path or not os.path.exists(path):
        print("No Claude Code session transcript found for this directory; build the handover from context only.")
        return

    tools = {}          # tool_use_id -> (name, input summary)
    humans = []         # (ts, text, compaction_index)
    denials, interrupts, commands, background = [], [], [], []
    edited, read = Counter(), Counter()
    compactions, first_ts, last_ts, branch = [], None, None, None
    last_tool = None

    for e in load(path):
        if e.get("isSidechain"):
            continue
        first_ts = first_ts or e.get("timestamp")
        last_ts = e.get("timestamp") or last_ts
        branch = e.get("gitBranch") or branch
        kind = e.get("type")

        if kind == "system" and e.get("subtype") == "compact_boundary":
            compactions.append(ts(e))
            continue

        if kind == "assistant":
            for b in e.get("message", {}).get("content", []) or []:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                name, inp = b.get("name", "?"), b.get("input", {})
                tools[b.get("id")] = (name, summarize_input(name, inp))
                last_tool = f"{name}({summarize_input(name, inp)})"
                if name in EDIT_TOOLS and isinstance(inp, dict):
                    edited[inp.get("file_path") or inp.get("notebook_path") or "?"] += 1
                if name == "Read" and isinstance(inp, dict) and inp.get("file_path"):
                    read[inp["file_path"]] += 1
                if name in SHELL_TOOLS and isinstance(inp, dict):
                    cmd = str(inp.get("command", ""))
                    commands.append((ts(e), cmd))
                    if inp.get("run_in_background") or BACKGROUND.search(cmd):
                        background.append((ts(e), cmd))
            continue

        if kind == "attachment":  # messages the user typed while the agent was mid-turn
            att = e.get("attachment") or {}
            if att.get("type") == "queued_command" and (att.get("origin") or {}).get("kind", "human") == "human":
                text = NOISE.sub("", text_of(att.get("prompt") or "")).strip()
                if text and not text.startswith("<task-notification"):
                    humans.append((ts(e), "(mid-turn) " + text, len(compactions)))
            continue

        if kind != "user" or e.get("isMeta") or e.get("isCompactSummary"):
            continue
        content = e.get("message", {}).get("content", "")

        for b in content if isinstance(content, list) else []:
            if not (isinstance(b, dict) and b.get("type") == "tool_result"):
                continue
            raw = b.get("content")
            raw = raw if isinstance(raw, str) else text_of(raw or [])
            name, summ = tools.get(b.get("tool_use_id"), ("?", ""))
            if e.get("toolDenialKind") == "user-rejected":
                reason = raw.split("the following reason", 1)[1] if "the following reason" in raw else ""
                item = (ts(e), f"{name}({summ})", short(reason.lstrip(": \n"), 300))
                if not denials or denials[-1][1:] != item[1:]:
                    denials.append(item)
            elif name == "AskUserQuestion" and not b.get("is_error"):
                humans.append((ts(e), "(answered a question) " + raw.split("answered:", 1)[-1], len(compactions)))

        origin = (e.get("origin") or {}).get("kind")
        if origin not in (None, "human"):
            continue
        text = NOISE.sub("", text_of(content)).strip()
        if not text or text.startswith(("<command-name>", "<local-command", "Caveat:", "<task-notification")):
            continue
        if text.startswith("[Request interrupted"):
            interrupts.append([ts(e), last_tool or "?", ""])
            continue
        if interrupts and not interrupts[-1][2]:
            interrupts[-1][2] = short(text, 300)
        humans.append((ts(e), text, len(compactions)))

    n_comp = len(compactions)
    out = [
        "# Session digest",
        f"- File: `{path}`",
        f"- Span: {(first_ts or '?')[:16]} → {(last_ts or '?')[:16]} UTC · branch: {branch or '?'}",
        f"- Human messages: {len(humans)} · compactions: {n_comp}"
        + (f" (last at {compactions[-1]})" if n_comp else ""),
    ]
    if n_comp:
        out.append("> [pre-compaction] messages are NO LONGER in the live context. Mine them first: early corrections live there.")

    # Small, high-value sections are rendered first; human messages fill the remaining budget.
    tail = []
    if denials:
        tail.append("\n## Tool calls the user rejected")
        tail.extend(f"- {t} {call} — reason: {reason or '(none given)'}" for t, call, reason in denials[-30:])
    if interrupts:
        tail.append("\n## Interruptions (user stopped the agent)")
        tail.extend(f"- {t} during {tool} → next user message: {nxt or '(none)'}" for t, tool, nxt in interrupts[-30:])
    if edited:
        tail.append(f"\n## Files edited ({len(edited)})")
        tail.extend(f"- `{p}` ×{n}" for p, n in edited.most_common(40))
    if read:
        others = [(p, n) for p, n in read.most_common(25) if p not in edited]
        if others:
            tail.append(f"\n## Files read, not edited ({len(others)}) — candidates for the handover's required reading")
            tail.extend(f"- `{p}` ×{n}" for p, n in others)
    if background:
        tail.append("\n## Possibly still running (background / scheduler commands) — verify before claiming")
        tail.extend(f"- {t} `{short(c, 200)}`" for t, c in background[-15:])
    if commands:
        tail.append("\n## Last shell commands")
        tail.extend(f"- {t} `{short(c, 160)}`" for t, c in commands[-15:])

    budget = args.max_chars - sum(len(x) + 1 for x in out + tail) - 200
    # (flagged, pre-compaction, other) character limits; 0 = omit. Degrade until it fits.
    for limits in [(800, 300, 150), (500, 200, 0), (300, 100, 0), (200, 0, 0), (120, 0, 0)]:
        body, omitted = [], 0
        for t, text, ci in humans:
            pre = ci < n_comp
            flag = text.startswith("(answered") or bool(CORRECTION.search(text))
            limit = limits[0] if flag else (limits[1] if pre else limits[2])
            if limit:
                body.append(f"- {'[pre-compaction] ' if pre else ''}{'⚑ ' if flag else ''}{t} — {short(text, limit)}")
            else:
                omitted += 1
        if sum(len(x) + 1 for x in body) <= budget:
            break
    out.append("\n## Human messages (chronological; ⚑ = likely correction/preference)")
    out.extend(body)
    if omitted:
        out.append(f"- …{omitted} unflagged messages omitted for length (raise --max-chars to see them)")
    print("\n".join(out + tail))


if __name__ == "__main__":
    main()
