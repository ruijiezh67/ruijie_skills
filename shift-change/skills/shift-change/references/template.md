# Handover template

Fill in this order. Tier 1 is never skipped; drop any Tier 2/3 section that has nothing real in it. The I-PASS letters show where each part comes from: **I**llness severity → Status, **P**atient summary → Picture, **A**ction list → Next actions, **S**ituation awareness & contingencies → no-go zones, traps, running jobs, if–then; **S**ynthesis by receiver → the exam and `/shift-start`.

Tags: `[verified: <command> → <result>]` · `[assumed]` · `[user said]`.

```markdown
# Shift handover: <project> · <YYYY-MM-DD HH:MM>
> Receiver: run /shift-start first. Read every file under "Read these first", then read back before acting.
> Previous handover: <path or none> · Next-session goal: <from the user, if given>

## 0 · Read these first (required)
| File | What it governs | Why it matters now |
|---|---|---|
| `<path>` | <e.g. the figure standards we agreed on> | <e.g. every plot in the next step must follow it> |

Reference, read only if needed: `<path>` (<what it is>), …

## 1 · Status  (I)
🟢/🟡/🔴 <one line: how healthy or fragile the work is right now, and why>
Deadline: <date: what is due, for whom> (omit if none)

## 2 · Picture  (P)
<3–6 sentences: the goal, why it matters, what has been achieved, where we are stuck.>

**Mental map** (what we currently believe and are testing; say whose view each is):
- H1 (user's working hypothesis): <hypothesis> · for: <evidence> · against: <evidence> · next test: <what would settle it>
- H2 (agent's alternative, not accepted by the user): …
- Disagreement: <where the user and agent read the evidence differently, if anywhere>


## 3 · Next actions  (A)
1. <concrete action> · done when <observable condition>
2. …

## 4 · No-go zones
| Rejected path | Why it was rejected | Reopen only if |
|---|---|---|
| <e.g. lowering lr to 1e-5> | <diverged anyway at step 3k; see run 17> [verified: …] | <data pipeline changes> |

## 5 · Working with <user>  (who they are, and taste)
**About the user**: facts they shared about themselves, each with the date if it changed:
- <e.g. PhD student in computational biology; works mostly in R; advisor wants weekly figures> [user said, 2026-03-02]
- <e.g. learning Spanish and French; moving to Lyon in June> [user said]

| I assumed | User corrected | Rule from now on | User's words |
|---|---|---|---|
| <wrote a 40-line explanation> | <wanted the answer first> | <lead with the answer, ≤5 lines, details only on request> | "conclusion first" |

## 6 · Evidence ledger
| Claim | Status | Evidence |
|---|---|---|
| <baseline acc = 71.2%> | verified | `python eval.py --ckpt c17` → 71.2 |
| <acc = 68.4% in results/old.csv> | superseded (stale) | <computed before the split fix; do not cite> |
| <the drop comes from tokenization> | assumed | <only one run so far> |
| <does it hold on MATH500?> | unknown | not run |

## 6b · What I told or made for the user
- <specific numbers, recommendations, names or content you gave them that they may ask about again, e.g. "recommended 1:10 tea-tree-to-carrier-oil dilution", "reported p = 0.013 for the interaction term", "draft abstract v2 is in paper/abstract.md">

## 7 · Experiment details
- Run: `<exact command>` · env: <conda env / module loads / GPU> · seed: <n> · data: <version or path> · config: <file> · output: <path>

## 8 · Running right now
| What | ID / where | Output lands at | Check when / how |
|---|---|---|---|
| <sweep over lr> | <slurm 481516 on greatlakes> | <runs/sweep3/> | <~2h; `squeue -j 481516`> |

## 9 · Gotchas
- <trap> → <what to do instead> (e.g. "GPU 3 on node7 throws ECC errors → exclude it")

## 10 · Jargon
| Term | Means | Not to be confused with |
|---|---|---|
| <"the clean set"> | <data/v3_dedup.jsonl, 4,812 rows> | <data/v3.jsonl, which has duplicates> |

## 11 · Context
- Pressure: <advisor / reviewer asks, what this feeds: which paper, which figure>
- File map: `<path>`: <role> (only files the next session will actually touch)
- If–then: if <X happens>, then <Y>.

---
Handover fidelity: <n>/<N> (<k> patch rounds) · Known gaps: <what the exam could not close, or "none">
```

## Length

Say what is needed and nothing more. A session of a few hours usually lands at 60–200 lines. If Tier 1 alone exceeds a screen, the picture paragraph is probably doing a history lesson; cut it to where we are *now*.
