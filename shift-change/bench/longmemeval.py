#!/usr/bin/env python3
"""Handover benchmark on LongMemEval (Wu et al., ICLR 2025): official data, official answers, official judge prompts.

For each sampled question:
  1. The question's official chat history (all evidence sessions plus a seeded sample of its
     official distractor sessions, capped at --chars, original order kept) is written verbatim as a
     Claude Code session transcript. No turn is generated or edited.
  2. Each condition forks that session and writes a handover (same as run.py).
  3. A fresh agent that never saw the history answers the official question from the handover
     alone, given the official question date.
  4. The official LongMemEval judge prompt (evaluate_qa.py, per question type) grades the answer
     yes/no. The official judge model is gpt-4o; here the same prompts run on Claude.

Extra condition `full-history`: the answering agent reads the whole (capped) history directly,
the usual upper reference in LongMemEval.

Data: https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned (MIT), file
longmemeval_s_cleaned.json, downloaded to .work/data/.

Usage:
  python longmemeval.py --per-type 3 --abstention 3 --jobs 2
  python longmemeval.py --summarize
"""
import argparse
import datetime
import glob
import json
import os
import random
import re
import subprocess
import sys
import urllib.request
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import run  # reuse the harness: claude(), handover(), install_skills(), dump(), rmtree(), ...

DATA_URL = "https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_s_cleaned.json"
DATA = os.path.join(run.WORK, "data", "longmemeval_s_cleaned.json")
RESULTS_ROOT = os.environ.get("SHIFT_LME_RESULTS") or os.path.join(run.HERE, "results-longmemeval")
RESULTS = os.path.join(RESULTS_ROOT, "test")  # set from --split in main()
SEEDS = {"dev": 2025, "test": 2026}  # dev: used while improving the skill; test: disjoint, reported
CONDITIONS = ["none", "full-history", "compact", "pocock-handoff", "remvisual-handoff", "shift-change-quick", "shift-change"]
TYPES = ["single-session-user", "single-session-assistant", "single-session-preference",
         "multi-session", "knowledge-update", "temporal-reasoning"]

# ---- official judge prompts, verbatim from LongMemEval src/evaluation/evaluate_qa.py (MIT) ----
JUDGE = {
    "default": "I will give you a question, a correct answer, and a response from a model. Please answer yes if the response contains the correct answer. Otherwise, answer no. If the response is equivalent to the correct answer or contains all the intermediate steps to get the correct answer, you should also answer yes. If the response only contains a subset of the information required by the answer, answer no. \n\nQuestion: {}\n\nCorrect Answer: {}\n\nModel Response: {}\n\nIs the model response correct? Answer yes or no only.",
    "temporal-reasoning": "I will give you a question, a correct answer, and a response from a model. Please answer yes if the response contains the correct answer. Otherwise, answer no. If the response is equivalent to the correct answer or contains all the intermediate steps to get the correct answer, you should also answer yes. If the response only contains a subset of the information required by the answer, answer no. In addition, do not penalize off-by-one errors for the number of days. If the question asks for the number of days/weeks/months, etc., and the model makes off-by-one errors (e.g., predicting 19 days when the answer is 18), the model's response is still correct. \n\nQuestion: {}\n\nCorrect Answer: {}\n\nModel Response: {}\n\nIs the model response correct? Answer yes or no only.",
    "knowledge-update": "I will give you a question, a correct answer, and a response from a model. Please answer yes if the response contains the correct answer. Otherwise, answer no. If the response contains some previous information along with an updated answer, the response should be considered as correct as long as the updated answer is the required answer.\n\nQuestion: {}\n\nCorrect Answer: {}\n\nModel Response: {}\n\nIs the model response correct? Answer yes or no only.",
    "single-session-preference": "I will give you a question, a rubric for desired personalized response, and a response from a model. Please answer yes if the response satisfies the desired response. Otherwise, answer no. The model does not need to reflect all the points in the rubric. The response is correct as long as it recalls and utilizes the user's personal information correctly.\n\nQuestion: {}\n\nRubric: {}\n\nModel Response: {}\n\nIs the model response correct? Answer yes or no only.",
    "abstention": "I will give you an unanswerable question, an explanation, and a response from a model. Please answer yes if the model correctly identifies the question as unanswerable. The model could say that the information is incomplete, or some other information is given but the asked information is not.\n\nQuestion: {}\n\nExplanation: {}\n\nModel Response: {}\n\nDoes the model correctly identify the question as unanswerable? Answer yes or no only.",
}

# ---- official reading prompts, verbatim from LongMemEval src/generation/run_generation.py (MIT) ----
# full history: the "History Chats" template; handover notes: the "facts extracted from history chats" template;
# no handover: the official no-retrieval setting, which passes the question alone.
ANSWER_FULL = ("I will give you several history chats between you and a user. Please answer the question based on the "
               "relevant chat history.\n\n\nHistory Chats:\n\n{}\n\nCurrent Date: {}\nQuestion: {}\nAnswer:")
ANSWER_HANDOVER = ("I will give you several facts extracted from history chats between you and a user. Please answer the "
                   "question based on the relevant facts.\n\n\nHistory Chats:\n\n{}\n\nCurrent Date: {}\nQuestion: {}\nAnswer:")
ANSWER_NONE = "{}"


def is_abstention(q):
    return q["question_id"].endswith("_abs")


def load_sample(per_type, n_abs, seed, exclude=()):
    if not os.path.exists(DATA):
        os.makedirs(os.path.dirname(DATA), exist_ok=True)
        run.log(f"downloading {DATA_URL}")
        urllib.request.urlretrieve(DATA_URL, DATA)
    data = json.load(open(DATA, encoding="utf-8"))
    rng = random.Random(seed)
    picked = []
    for t in TYPES:
        pool = sorted((q for q in data if q["question_type"] == t and not is_abstention(q)
                       and q["question_id"] not in exclude), key=lambda q: q["question_id"])
        picked += rng.sample(pool, per_type)
    abs_pool = sorted((q for q in data if is_abstention(q) and q["question_id"] not in exclude), key=lambda q: q["question_id"])
    picked += rng.sample(abs_pool, n_abs)
    return picked


def history(q, max_chars, seed):
    """All evidence sessions plus a seeded sample of the question's own distractor sessions, in original order."""
    sessions = list(zip(q["haystack_session_ids"], q["haystack_dates"], q["haystack_sessions"]))
    size = lambda s: sum(len(t["content"]) for t in s[2])
    keep = {i for i, s in enumerate(sessions) if s[0] in q["answer_session_ids"]}
    total = sum(size(sessions[i]) for i in keep)
    others = [i for i in range(len(sessions)) if i not in keep]
    random.Random(f"{seed}:{q['question_id']}").shuffle(others)
    for i in others:
        if total + size(sessions[i]) > max_chars:
            continue
        keep.add(i)
        total += size(sessions[i])
    return [sessions[i] for i in sorted(keep)], total


def parse_date(s):
    return datetime.datetime.strptime(re.sub(r"\s*\(\w+\)\s*", " ", s).strip(), "%Y/%m/%d %H:%M")


def write_transcript(sessions, cwd, session_id):
    """The official turns, verbatim, as a resumable Claude Code session (each session opens with its date)."""
    pdir = run.project_dir(cwd)
    os.makedirs(pdir, exist_ok=True)
    prev = None
    with open(os.path.join(pdir, session_id + ".jsonl"), "w", encoding="utf-8") as f:
        for _, date, turns in sessions:
            t = parse_date(date)
            for j, turn in enumerate(turns):
                u = str(uuid.uuid4())
                text = turn["content"] if j else f"[Chat session on {date}]\n{turn['content']}"
                e = {"parentUuid": prev, "isSidechain": False, "userType": "external", "cwd": cwd, "sessionId": session_id,
                     "version": "2.1.92", "gitBranch": "", "uuid": u, "type": turn["role"],
                     "timestamp": (t + datetime.timedelta(seconds=30 * j)).isoformat() + "Z"}
                if turn["role"] == "user":
                    e["message"] = {"role": "user", "content": text}
                else:
                    e["message"] = {"id": "msg_" + u[:12], "type": "message", "role": "assistant", "model": "longmemeval-history",
                                    "content": [{"type": "text", "text": text}], "stop_reason": "end_turn",
                                    "stop_sequence": None, "usage": {"input_tokens": 0, "output_tokens": 0}}
                    e["requestId"] = "req_" + u[:12]
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
                prev = u


def format_history(sessions):
    """Official 'nl' session format (run_generation.py, retriever_type=orig-session)."""
    out = ""
    for k, (_, date, turns) in enumerate(sessions, 1):
        body = "".join("\n\n{}: {}".format(t["role"], t["content"].strip()) for t in turns)
        out += "\n### Session {}:\nSession Date: {}\nSession Content:\n{}\n".format(k, date, body)
    return out


def judge(q, response, cwd):
    key = "abstention" if is_abstention(q) else (q["question_type"] if q["question_type"] in JUDGE else "default")
    prompt = JUDGE[key].format(q["question"], q["answer"], response)
    out = run.claude(["--permission-mode", "dontAsk"], cwd, prompt, timeout=600)
    text = (out.get("result") or "").strip().lower()
    if not text.startswith(("yes", "no")):
        out = run.claude(["--permission-mode", "dontAsk"], cwd, prompt, timeout=600)
        text = (out.get("result") or "").strip().lower()
    return ("yes" if text.startswith("yes") else "no" if text.startswith("no") else None), out.get("result", "")


def run_one(q, cond, max_chars, seed):
    qid = q["question_id"]
    out_path = os.path.join(RESULTS, "runs", f"{qid}__{cond['name']}.json")
    if os.path.exists(out_path) or run.LIMIT.is_set():
        return
    run_dir = os.path.join(run.WORK, "lme", qid, cond["name"])
    exam_dir = run_dir + "-exam"
    try:
        sessions, chars = history(q, max_chars, seed)
        run.rmtree(run_dir)
        os.makedirs(run_dir)
        run.git(run_dir, "init", "-q")
        run.git(run_dir, "-c", "user.name=bench", "-c", "user.email=bench@local", "commit", "-q", "--allow-empty", "-m", "start")
        sid = str(uuid.uuid4())
        write_transcript(sessions, run_dir, sid)
        run.log(f"  {qid} · {cond['name']}: handover…")
        if cond["name"] == "full-history":
            h = {"artifact": "", "artifact_source": "full-history", "pins": {}, "wall_s": 0, "cost_usd": 0}
            prompt = ANSWER_FULL.format(format_history(sessions), q["question_date"], q["question"])
        else:
            h = run.handover(cond, {"session_id": sid}, run_dir)
            prompt = (ANSWER_NONE.format(q["question"]) if cond["name"] == "none" else
                      ANSWER_HANDOVER.format(h["artifact"], q["question_date"], q["question"]))
        os.makedirs(exam_dir, exist_ok=True)
        ans = run.claude(["--permission-mode", "dontAsk"], exam_dir, prompt, timeout=900)
        answer = ans.get("result", "")
        verdict, judge_raw = judge(q, answer, exam_dir) if answer else (None, "")
        if run.LIMIT.is_set():  # a quota stop is not a result; this run will simply be redone next time
            return
        problems = [p for p, bad in [("no artifact", cond["prompt"] and h["artifact_source"] == "missing"),
                                     ("no answer", not answer or bool(run.LIMIT_RX.search(answer))),
                                     ("no verdict", verdict is None)] if bad]
        run.log(f"  {qid} · {cond['name']}: {verdict} (artifact {len(h['artifact'])} chars)"
                + (f"  ⚠ INVALID ({', '.join(problems)})" if problems else ""))
        if problems:
            out_path = os.path.join(RESULTS, "failed", f"{qid}__{cond['name']}__{int(datetime.datetime.now().timestamp())}.json")
        run.dump({"question_id": qid, "question_type": q["question_type"], "abstention": is_abstention(q),
                  "condition": cond["name"], "history_chars": chars, "history_sessions": len(sessions),
                  "pins": h["pins"], "artifact": h["artifact"], "artifact_source": h["artifact_source"],
                  "handover_wall_s": h["wall_s"], "handover_cost_usd": h.get("cost_usd"),
                  "question": q["question"], "question_date": q["question_date"], "gold": q["answer"],
                  "answer": answer, "verdict": verdict, "judge_raw": judge_raw}, out_path)
    except Exception as e:
        run.log(f"  {qid} · {cond['name']}: FAILED {type(e).__name__}: {e}")
    finally:
        run.rmtree(run_dir)
        run.rmtree(exam_dir)
        for d in (run_dir, exam_dir):  # the written history and the forked handover sessions are test artifacts
            run.rmtree(run.project_dir(d))


def summarize():
    rows = defaultdict(list)
    for f in glob.glob(os.path.join(RESULTS, "runs", "*.json")):
        r = json.load(open(f, encoding="utf-8"))
        rows[r["condition"]].append(r)
    cats = TYPES + ["abstention"]
    cat = lambda r: "abstention" if r["abstention"] else r["question_type"]
    lines = ["# LongMemEval handover results", "",
             "Accuracy = share of questions judged correct by the official LongMemEval judge prompt (run on Claude). "
             "One run per question and condition.", "",
             "| Condition | questions | Accuracy | " + " | ".join(cats) + " | Handover chars (median) | Handover time (s, median) |",
             "|---|---|---|" + "---|" * len(cats) + "---|---|"]
    for name in [c for c in CONDITIONS if c in rows]:
        rs = rows[name]
        acc = lambda xs: f"{sum(r['verdict'] == 'yes' for r in xs) / len(xs):.2f}" if xs else "–"
        med = lambda v: sorted(v)[len(v) // 2] if v else 0
        cells = [acc(rs)] + [acc([r for r in rs if cat(r) == c]) for c in cats]
        lines.append(f"| {name} | {len(rs)} | " + " | ".join(cells)
                     + f" | {med([len(r['artifact']) for r in rs])} | {med([r['handover_wall_s'] for r in rs]):.0f} |")
    failed = glob.glob(os.path.join(RESULTS, "failed", "*.json"))
    if failed:
        lines += ["", f"{len(failed)} runs failed for infrastructure reasons and were re-run; kept in `failed/`."]
    os.makedirs(RESULTS, exist_ok=True)
    open(os.path.join(RESULTS, "summary.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-type", type=int, default=3, help="questions sampled per question type")
    ap.add_argument("--abstention", type=int, default=3, help="abstention questions sampled")
    ap.add_argument("--chars", type=int, default=100_000, help="history size cap (evidence sessions always kept)")
    ap.add_argument("--split", choices=["dev", "test"], default="test",
                    help="dev: questions used while improving the skill; test: a disjoint sample, the reported numbers")
    ap.add_argument("--conditions", help="comma-separated subset of: " + ",".join(CONDITIONS))
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--question", action="append", help="only these question ids (from the sample)")
    ap.add_argument("--summarize", action="store_true")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    global RESULTS
    RESULTS = os.path.join(RESULTS_ROOT, args.split)
    if args.summarize:
        return summarize()
    by_name = {c["name"]: c for c in json.load(open(os.path.join(run.HERE, "conditions.json"), encoding="utf-8"))}
    by_name["full-history"] = {"name": "full-history", "prompt": None}
    names = args.conditions.split(",") if args.conditions else CONDITIONS
    exclude = ()
    if args.split == "test":  # never report on a question that was looked at while developing
        exclude = {q["question_id"] for q in load_sample(args.per_type, args.abstention, SEEDS["dev"])}
    questions = load_sample(args.per_type, args.abstention, SEEDS[args.split], exclude)
    args.seed = SEEDS[args.split]
    if args.question:
        questions = [q for q in questions if q["question_id"] in args.question]
    else:
        run.dump([{"question_id": q["question_id"], "question_type": q["question_type"]} for q in questions],
                 os.path.join(RESULTS, "sample.json"))
    jobs = [(q, by_name[n]) for q in questions for n in names]
    run.log(f"{len(questions)} questions × {len(names)} conditions = {len(jobs)} runs")
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        list(pool.map(lambda j: run_one(j[0], j[1], args.chars, args.seed), jobs))
    summarize()


if __name__ == "__main__":
    main()
