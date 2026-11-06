#!/usr/bin/env python3
"""Handover fidelity benchmark.

For each scripted research session:
  1. build    Replay the scripted user turns with `claude -p` in a scratch git repo,
              producing a real Claude Code session (once per session, then reused).
              The finished repo is frozen as a bare git snapshot.
  2. handover For each condition and repeat, clone a fresh copy of the snapshot, fork the
              session into it (`--resume <id> --fork-session`), install the condition's
              skill, and ask for a handover. Capture the artifact.
  3. exam     In another fresh clone, an agent that never saw the session gets only the
              artifact plus the repository, and answers the held-out questions.
  4. grade    An LLM grader scores each answer against the answer key (1 / 0.5 / 0).

Every run gets its own directories, so runs cannot contaminate each other and can run
in parallel (--jobs).

Usage:
  python run.py --session ml-divergence --conditions none,shift-change --repeats 3
  python run.py --summarize            # rebuild results/summary.md from saved runs
Standard library only. Needs `git` and the `claude` CLI on PATH, logged in.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
WORK = os.path.join(HERE, ".work")
PROJECTS = os.path.join(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude"), "projects")
BUILD_TOOLS = "Read Edit Write Glob Grep Bash(python:*) Bash(python3:*) Bash(git:*) Bash(ls:*) Bash(cat:*) Bash(head:*) Bash(tail:*) Bash(grep:*)"
# No "Skill": a condition's own skill runs through its slash command; the Skill tool would let a handover
# reach for other installed skills (e.g. a globally installed shift-change) and blur the comparison.
HANDOVER_TOOLS = BUILD_TOOLS + " Agent Task Bash(mkdir:*) Bash(cp:*) Bash(date:*) Bash(squeue:*) Bash(nvidia-smi:*)"
HANDOVER_NOTE = (
    "This is a non-interactive benchmark run. Nobody will answer questions, so do not ask any. "
    "Do not write to CLAUDE.md, AGENTS.md or any memory file. When you have finished writing the "
    "handover document, print its absolute path on the final line as HANDOFF_PATH=<path>."
)
_print_lock = threading.Lock()
LIMIT = threading.Event()  # set when the account hits its usage limit: stop starting new work


def log(msg):
    with _print_lock:
        print(msg, flush=True)


_VERSION = []


def claude_version():
    if not _VERSION:
        try:
            _VERSION.append(subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=60).stdout.strip())
        except Exception:
            _VERSION.append("N/A")
    return _VERSION[0]


def claude(args, cwd, prompt, timeout=3600, append_system=None, isolate=False, persist=False):
    """isolate=True keeps the benchmark operator's own setup out of every arm: no user or local settings
    (so no installed plugins, hooks or user skills), no MCP servers, no CLAUDE.md at any level, no session
    file (persist=True keeps it, for --resume). Verified 2026-10-27: without CLAUDE_CODE_DISABLE_CLAUDE_MDS the user's ~/.claude/CLAUDE.md still
    reaches the model even with --setting-sources project. Skills in <cwd>/.claude/skills still load."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDECODE") and k != "CLAUDE_CODE_ENTRYPOINT"}
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    if isolate:
        env["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] = "1"
        args = ["--setting-sources", "project", "--strict-mcp-config"] + ([] if persist else ["--no-session-persistence"]) + list(args)
    cmd = ["claude", "-p", "--output-format", "json"] + args
    if append_system:
        cmd += ["--append-system-prompt", append_system]
    t0 = time.time()
    proc = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8", errors="replace", env=env)
    try:
        stdout, stderr = proc.communicate(prompt, timeout=timeout)
        try:
            out = json.loads(stdout)
        except ValueError:
            out = {"result": stdout, "is_error": True, "stderr": stderr[-2000:]}
    except subprocess.TimeoutExpired:
        # kill the whole tree: subagents keep the pipes open otherwise
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.kill()
        proc.communicate()
        out = {"result": "", "is_error": True, "stderr": f"timeout after {timeout}s"}
    out["wall_s"] = round(time.time() - t0, 1)
    out["claude_version"] = claude_version()
    out["models"] = sorted((out.get("modelUsage") or {}).keys())  # results must say what produced them
    if "hit your limit" in (out.get("result") or "") or "hit your limit" in (out.get("stderr") or ""):
        if not LIMIT.is_set():
            log(f"  usage limit reached ({(out.get('result') or '').strip()[:80]}); finishing without starting new runs")
        LIMIT.set()
    return out


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True).stdout.strip()


def rmtree(path):
    """Delete a tree, including git's read-only object files on Windows."""
    def force(func, p, _):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    if os.path.exists(path):
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=force)
        else:
            shutil.rmtree(path, onerror=force)


def project_dir(path):
    return os.path.join(PROJECTS, re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path)))


def session_file(session_id):
    hits = glob.glob(os.path.join(PROJECTS, "*", f"{session_id}.jsonl"))
    return hits[0] if hits else None


def scrub(text):
    """Remove the local home directory and username from text that will be published."""
    home = os.path.expanduser("~")
    user = os.path.basename(home)
    for variant in {home, home.replace("\\", "/"), home.replace("\\", "\\\\"), home.replace("/", "\\\\")}:
        text = re.sub(re.escape(variant), "~", text, flags=re.I)
    return re.sub(rf"Users-{re.escape(user)}-", "Users-<user>-", text, flags=re.I)


def dump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(scrub(json.dumps(obj, ensure_ascii=False, indent=1)))


def extract_json(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except ValueError:
        return {}


# ---------- 1. build (once per session) ----------

def save_state(session, state):
    path = os.path.join(RESULTS, session, "build.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(state, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def freeze(state):
    """Make a bare git snapshot of the finished session repo (recovering from loose objects if needed)."""
    snap = os.path.join(WORK, "snapshots", state["session"] + ".git")
    if not os.path.isdir(snap):
        os.makedirs(os.path.dirname(snap), exist_ok=True)
        base = state["base"]
        if git(base, "rev-parse", "HEAD") == state["head"]:
            subprocess.run(["git", "clone", "-q", "--bare", base, snap], check=True)
        else:  # the working repo is damaged; rebuild the snapshot from its object store
            subprocess.run(["git", "init", "-q", "--bare", snap], check=True)
            shutil.copytree(os.path.join(base, ".git", "objects"), os.path.join(snap, "objects"), dirs_exist_ok=True)
            git(snap, "update-ref", "refs/heads/main", state["head"])
            git(snap, "symbolic-ref", "HEAD", "refs/heads/main")
        if git(snap, "rev-parse", "HEAD") != state["head"]:
            raise RuntimeError(f"snapshot for {state['session']} does not resolve to {state['head']}")
    state["snapshot"] = snap
    state["session_file"] = state.get("session_file") or session_file(state["session_id"])
    return state


def build(session):
    sdir = os.path.join(HERE, "sessions", session)
    state_path = os.path.join(RESULTS, session, "build.json")
    if os.path.exists(state_path):
        state = json.load(open(state_path, encoding="utf-8"))
        if "snapshot" not in state or not os.path.isdir(state["snapshot"]):
            state = freeze(state)
            save_state(session, state)
        return state

    spec = json.load(open(os.path.join(sdir, "session.json"), encoding="utf-8"))
    base = os.path.join(WORK, "base", session)
    rmtree(base)
    shutil.copytree(os.path.join(sdir, "repo"), base)
    git(base, "init", "-q")
    git(base, "add", "-A")
    git(base, "-c", "user.name=bench", "-c", "user.email=bench@local", "commit", "-qm", "initial")

    sid, turns = None, []
    for i, turn in enumerate(spec["turns"]):
        args = ["--permission-mode", "acceptEdits", "--allowedTools", BUILD_TOOLS]
        if sid:
            args += ["--resume", sid]
        log(f"  build turn {i + 1}/{len(spec['turns'])}: {turn[:60]}")
        out = claude(args, base, turn)
        sid = out.get("session_id", sid)
        turns.append({"user": turn, "assistant": out.get("result", ""), "wall_s": out["wall_s"],
                      "cost_usd": out.get("total_cost_usd")})

    git(base, "add", "-A")
    git(base, "-c", "user.name=bench", "-c", "user.email=bench@local", "commit", "-qm", "session end")
    sf = session_file(sid)
    compactions = sum('"compact_boundary"' in line for line in open(sf, encoding="utf-8")) if sf else 0
    state = {"session": session, "session_id": sid, "base": base, "head": git(base, "rev-parse", "HEAD"),
             "session_file": sf, "compactions": compactions, "turns": turns}
    state = freeze(state)
    save_state(session, state)
    log(f"  built session {sid} (compactions: {compactions})")
    return state


def checkout(state, dest):
    """A fresh working copy of the frozen session repo, plus the session transcript so --resume finds it."""
    rmtree(dest)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    subprocess.run(["git", "clone", "-q", state["snapshot"], dest], check=True)
    if git(dest, "rev-parse", "HEAD") != state["head"] or git(dest, "status", "--porcelain"):
        raise RuntimeError(f"checkout {dest} is not a clean copy of {state['head']}")
    pdir = project_dir(dest)
    os.makedirs(pdir, exist_ok=True)
    shutil.copy2(state["session_file"], os.path.join(pdir, os.path.basename(state["session_file"])))
    return dest


# ---------- 2. handover ----------

def fetch_github_dir(repo, path, dest):
    with urllib.request.urlopen(f"https://api.github.com/repos/{repo}/commits?path={path}&per_page=1") as r:
        sha = json.load(r)[0]["sha"]

    def fetch(p, d):
        with urllib.request.urlopen(f"https://api.github.com/repos/{repo}/contents/{p}?ref={sha}") as r:
            items = json.load(r)
        os.makedirs(d, exist_ok=True)
        for it in items:
            if it["type"] == "file":
                urllib.request.urlretrieve(it["download_url"], os.path.join(d, it["name"]))
            elif it["type"] == "dir":
                fetch(it["path"], os.path.join(d, it["name"]))
    fetch(path, dest)
    return sha


def install_skills(cond, run_dir):
    pins = {}
    for s in cond.get("skills", []):
        if s.get("kind") == "command":  # a single slash-command file: .claude/commands/<as>.md
            os.makedirs(os.path.join(run_dir, ".claude", "commands"), exist_ok=True)
            with urllib.request.urlopen(f'https://api.github.com/repos/{s["github"]}/commits?path={s["path"]}&per_page=1') as r:
                sha = json.load(r)[0]["sha"]
            urllib.request.urlretrieve(f'https://raw.githubusercontent.com/{s["github"]}/{sha}/{s["path"]}',
                                       os.path.join(run_dir, ".claude", "commands", s["as"] + ".md"))
            pins[s["as"]] = f'{s["github"]}@{sha[:10]}'
            continue
        dest = os.path.join(run_dir, ".claude", "skills", s["as"])
        if "local" in s:
            src = os.path.normpath(os.path.join(HERE, s["local"]))
            shutil.copytree(src, dest)
            digest = hashlib.sha256()
            for f in sorted(glob.glob(os.path.join(src, "**", "*"), recursive=True)):
                if os.path.isfile(f):
                    digest.update(open(f, "rb").read())
            pins[s["as"]] = "local@" + digest.hexdigest()[:10]  # which version of the skill produced this run
        else:
            pins[s["as"]] = f'{s["github"]}@{fetch_github_dir(s["github"], s["path"], dest)[:10]}'
    return pins


def compact_summary(session_id):
    sf = session_file(session_id)
    text = ""
    for line in open(sf, encoding="utf-8") if sf else []:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("isCompactSummary"):
            c = e.get("message", {}).get("content", "")
            text = c if isinstance(c, str) else "\n".join(b.get("text", "") for b in c if isinstance(b, dict))
    return text


def handover(cond, state, run_dir):
    pins = install_skills(cond, run_dir)
    if not cond["prompt"]:
        return {"artifact": "", "artifact_source": "none", "pins": pins, "wall_s": 0, "cost_usd": 0}
    before = time.time()
    out = claude(["--resume", state["session_id"], "--fork-session", "--permission-mode", "acceptEdits",
                  "--allowedTools", HANDOVER_TOOLS], run_dir, cond["prompt"], timeout=1800,
                 append_system=None if cond["name"] == "compact" else HANDOVER_NOTE)
    source, artifact = "", ""
    if cond["name"] == "compact":
        artifact, source = compact_summary(out.get("session_id", "")), "compact-summary"
    else:
        m = re.findall(r"HANDOFF_PATH=(.+)", out.get("result", ""))
        path = m[-1].strip().strip("`'\"*") if m else ""
        if path and not os.path.isabs(path):
            path = os.path.join(run_dir, path)
        source = "HANDOFF_PATH"
        if not os.path.isfile(path):  # fall back to the newest markdown written during the run
            cands = [f for f in glob.glob(os.path.join(run_dir, "**", "*.md"), recursive=True)
                     + glob.glob(os.path.join(tempfile.gettempdir(), "*.md"))
                     if os.path.getmtime(f) >= before and os.sep + ".claude" + os.sep not in f]
            path = max(cands, key=os.path.getmtime) if cands else ""
            source = "fallback:newest-md" if path else "missing"
        artifact = open(path, encoding="utf-8", errors="replace").read() if path else ""
    return {"artifact": artifact, "artifact_source": source, "pins": pins, "wall_s": out["wall_s"],
            "cost_usd": out.get("total_cost_usd"), "final_message": out.get("result", "")[-3000:]}


# ---------- 3. exam and 4. grade ----------

EXAM = """You are taking over a software/research project that you have never seen before.
{handover_block}
You may read files in the current repository. Do not read anything under ~/.claude/ or any chat logs.
Answer each question in 1-3 sentences. If you cannot tell from the handover or the repository,
answer exactly "NOT KNOWN" instead of guessing.

Questions:
{questions}

Reply with only a JSON object mapping each question id to your answer, e.g. {{"q1": "..."}}."""

GRADE = """You are grading a new team member's answers about a project against an answer key.
For each question give score 1 (all key points present, nothing contradicting the key),
0.5 (partly right: direction correct but a key point, reason or condition is missing), or
0 (wrong, contradicts the key, or "NOT KNOWN"). Judge substance, not wording or language.

{items}

Reply with only a JSON object: {{"q1": {{"score": 1, "why": "..."}}, ...}}."""

RETRY = "Your previous reply could not be parsed. Reply again with only the JSON object, nothing else."


def ask_json(args, cwd, prompt, expected_keys):
    """One claude call that must return a JSON object; retry once in the same session if it doesn't."""
    out = claude(args, cwd, prompt, timeout=1200)
    data, raw = extract_json(out.get("result", "")), [out.get("result", "") or out.get("stderr", "")]
    if not set(expected_keys) <= set(data):
        if out.get("session_id") and out.get("result"):  # it answered, but not as JSON: ask again in-session
            out2 = claude(args + ["--resume", out["session_id"]], cwd, RETRY, timeout=600)
        else:  # the call itself failed (empty output, rate limit, timeout): start over once
            out2 = claude(args, cwd, prompt, timeout=1200)
        data, raw = extract_json(out2.get("result", "")) or data, raw + [out2.get("result", "") or out2.get("stderr", "")]
    return data, raw, out["wall_s"]


def exam(artifact, questions, exam_dir):
    block = ("There is no handover document; the previous person left nothing." if not artifact.strip() else
             "The previous person left this handover document:\n<handover>\n" + artifact + "\n</handover>")
    qs = "\n".join(f'{q["id"]}. {q["q"]}' for q in questions)
    return ask_json(["--permission-mode", "dontAsk", "--allowedTools", "Read Glob Grep"], exam_dir,
                    EXAM.format(handover_block=block, questions=qs), [q["id"] for q in questions])


def grade(questions, answers, cwd):
    items = "\n\n".join(f'{q["id"]}. Question: {q["q"]}\nKey: {q["key"]}\nAnswer: {answers.get(q["id"], "NOT KNOWN")}'
                        for q in questions)
    data, raw, _ = ask_json(["--permission-mode", "dontAsk"], cwd, GRADE.format(items=items), [q["id"] for q in questions])
    return data, raw


def run_one(session, state, cond, k, questions):
    out_path = os.path.join(RESULTS, session, "runs", f"{cond['name']}-r{k}.json")
    if os.path.exists(out_path) or LIMIT.is_set():
        return
    run_dir = os.path.join(WORK, "runs", session, f"{cond['name']}-r{k}")
    exam_dir = run_dir + "-exam"
    try:
        log(f"  {session} · {cond['name']} r{k}: handover…")
        h = handover(cond, state, checkout(state, run_dir))
        answers, exam_raw, exam_s = exam(h["artifact"], questions, checkout(state, exam_dir))
        grades, grade_raw = grade(questions, answers, exam_dir)
        if LIMIT.is_set():  # a quota stop is not a result; this run will simply be redone next time
            return
        score = sum(g.get("score", 0) for g in grades.values())
        problems = [p for p, bad in [("no artifact", cond["prompt"] and h["artifact_source"] == "missing"),
                                     ("incomplete answers", len(answers) < len(questions)),
                                     ("incomplete grades", len(grades) < len(questions))] if bad]
        log(f"  {session} · {cond['name']} r{k}: {score}/{len(questions)} "
            f"(artifact {len(h['artifact'])} chars via {h['artifact_source']})"
            + (f"  ⚠ INVALID ({', '.join(problems)}), saved to failed/ and will rerun next time" if problems else ""))
        if problems:  # an infrastructure failure is not a score; keep it for inspection only
            out_path = os.path.join(RESULTS, session, "failed", f"{cond['name']}-r{k}-{int(time.time())}.json")
        dump({"session": session, "condition": cond["name"], "repeat": k, "pins": h["pins"],
                   "artifact": h["artifact"], "artifact_source": h["artifact_source"],
                   "handover_wall_s": h["wall_s"], "handover_cost_usd": h["cost_usd"],
                   "final_message": h.get("final_message", ""), "questions": questions, "answers": answers,
              "exam_raw": exam_raw, "grades": grades, "grade_raw": grade_raw, "exam_wall_s": exam_s}, out_path)
    except Exception as e:  # one broken run must not stop the others
        log(f"  {session} · {cond['name']} r{k}: FAILED {type(e).__name__}: {e}")
    finally:
        rmtree(run_dir)
        rmtree(exam_dir)


# ---------- summary ----------

def summarize():
    rows = defaultdict(list)
    for f in glob.glob(os.path.join(RESULTS, "*", "runs", "*.json")):
        r = json.load(open(f, encoding="utf-8"))
        rows[r["condition"]].append(r)
    order = [c["name"] for c in json.load(open(os.path.join(HERE, "conditions.json"), encoding="utf-8"))]
    cats = sorted({q["category"] for rs in rows.values() for r in rs for q in r["questions"]})
    sessions = sorted({r["session"] for rs in rows.values() for r in rs})
    failed = sorted(os.path.basename(f) for f in glob.glob(os.path.join(RESULTS, "*", "failed", "*.json")))
    lines = ["# Handover fidelity benchmark: results", "",
             "Score = share of points (1 / 0.5 / 0 per question). Overall is the mean ± SD over runs "
             "(sessions × repeats). `pre-compaction` = questions whose facts were stated before a mid-session /compact.", "",
             "| Condition | runs | Overall | " + " | ".join(sessions) + " | pre-compaction | " + " | ".join(cats)
             + " | Handover chars | Handover time (s, median) |",
             "|---|---|---|" + "---|" * (len(sessions) + 1 + len(cats)) + "---|---|"]
    for name in [c for c in order if c in rows]:
        rs = rows[name]

        def mean(pred, runs=rs):
            pts = [r["grades"].get(q["id"], {}).get("score", 0) for r in runs for q in r["questions"] if pred(q)]
            return f"{sum(pts) / len(pts):.2f}" if pts else "–"
        per_run = [sum(g.get("score", 0) for g in r["grades"].values()) / len(r["questions"]) for r in rs]
        mu = sum(per_run) / len(per_run)
        sd = (sum((x - mu) ** 2 for x in per_run) / (len(per_run) - 1)) ** 0.5 if len(per_run) > 1 else 0
        cells = [f"{mu:.2f} ± {sd:.2f}"]
        cells += [mean(lambda q: True, [r for r in rs if r["session"] == s]) for s in sessions]
        cells += [mean(lambda q: q.get("pre_compaction"))]
        cells += [mean(lambda q, c=c: q["category"] == c) for c in cats]
        chars = sum(len(r["artifact"]) for r in rs) // len(rs)
        secs = sorted(r["handover_wall_s"] for r in rs)[len(rs) // 2]  # median: one hung run shouldn't dominate
        lines.append(f"| {name} | {len(rs)} | " + " | ".join(cells) + f" | {chars} | {secs:.0f} |")
    if failed:
        lines += ["", f"Excluded as infrastructure failures and re-run ({len(failed)}): "
                  + ", ".join(failed) + ". Their files are kept in `results/<session>/failed/`."]
    open(os.path.join(RESULTS, "summary.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", action="append", help="session name(s) under sessions/ (default: all)")
    ap.add_argument("--conditions", help="comma-separated condition names (default: all)")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=3, help="runs in parallel")
    ap.add_argument("--summarize", action="store_true")
    ap.add_argument("--scrub", action="store_true", help="remove local paths/usernames from saved results")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    if args.scrub:
        for f in glob.glob(os.path.join(RESULTS, "**", "*.json"), recursive=True):
            if os.path.basename(f) == "build.json":  # local state, gitignored; needs real paths
                continue
            text = open(f, encoding="utf-8").read()
            open(f, "w", encoding="utf-8").write(scrub(text))
        return print("scrubbed")
    if args.summarize:
        return summarize()

    conds = json.load(open(os.path.join(HERE, "conditions.json"), encoding="utf-8"))
    if args.conditions:
        wanted = args.conditions.split(",")
        conds = [c for c in conds if c["name"] in wanted]
    sessions = args.session or sorted(os.listdir(os.path.join(HERE, "sessions")))
    jobs = []
    for session in sessions:
        log(f"== {session}")
        state = build(session)
        questions = json.load(open(os.path.join(HERE, "sessions", session, "questions.json"), encoding="utf-8"))
        jobs += [(session, state, c, k, questions) for k in range(1, args.repeats + 1) for c in conds]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        list(pool.map(lambda j: run_one(*j), jobs))
    summarize()


if __name__ == "__main__":
    main()
