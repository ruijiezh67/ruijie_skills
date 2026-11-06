# Launch thread (draft)

Numbers in `{{ }}` get filled from `bench/results-longmemeval/test/summary.md` and `bench/results/summary.md` before posting. Keep every claim checkable: each post that states a number links to the raw runs.

---

**1/ hook + demo**

> Hospitals cut handoff errors 23% with one rule: the incoming nurse reads the handoff back.
>
> I gave my coding agent the same rule.
>
> `/shift-change` writes the handover, then quizzes a fresh agent on it and patches what it missed — before you close the session.

*(attach: 25-second demo — exam scores 5/12, document gets patched, 12/12)*

---

**2/ the measurement**

> I didn't want to claim it was better, so I benchmarked it against 8 popular handoff skills and Claude Code's own /compact, on LongMemEval (ICLR 2025) — official questions, official answers, official judge prompts.
>
> 21 held-out questions, one handover each:
> shift-change 17/21 · mattpocock 16/21 · REMvisual 15/21 · /compact 14/21 · no handover 4/21
>
> And the number I'm not hiding: reading the full history scores 21/21.
>
> Raw runs, including the ones I lost to usage limits: https://github.com/ruijiezh67/ruijie_skills/tree/main/shift-change/bench

*(attach: the figure, `docs/assets/bench.svg`)*

---

**3/ what a handover usually loses**

> Three hours in, the agent knows you want the conclusion first, that lowering the LR was already tried, that "the clean set" is one specific file, that a sweep is running.
>
> A summary keeps *what was done*. It drops *how you want it done*.
>
> So the handover records your corrections as rules, in your own words, and tags every claim verified / assumed / unknown.

---

**4/ the failure that changed the design**

> The handover said "root cause located: no gradient clipping".
>
> That was the agent's conclusion. The user's hypothesis — fp16 overflow, with their own counter-evidence — had been quietly demoted.
>
> The agent writing the handover promotes its own reading. Now the mental map says whose hypothesis each one is, and the summary can't state as settled what the map lists as open.

---

**5/ the part I did not expect**

> It also doesn't paste your standards files into the handover. It lists them as required reading, and the next session has to open them.
>
> Summarising a standard is how a new session ends up "informed" about rules it has never read.

---

**6/ install + limits**

> ```
> npx skills add https://github.com/ruijiezh67/ruijie_skills/tree/main/shift-change/skills
> ```
> or `/plugin marketplace add ruijiezh67/ruijie_skills`
>
> Honest limits: a handover is compression. For details buried in a long session, reading the full history still wins (21/21 vs 17/21), and the lead over the next-best skill is one question — not a gap. /compact stays strong while you're in one session. What a handover buys is the part that was never in the code: your corrections, the paths you ruled out, the standards you agreed on.

---

## Reply-to-yourself follow-ups (use over the next days, not all at once)

- The benchmark harness itself: scripted sessions replayed as real Claude Code sessions, every run from a clean git snapshot, auto-memory disabled, usage-limit stops recorded rather than scored.
- The audit against Anthropic's published skill rules, and the one bug it caught that review missed: a colon inside a quoted trigger phrase broke the YAML frontmatter, so the skill would not have loaded at all.
- "How a researcher builds a skill with an agent": the CHANGELOG as the story, each rule traced to the failure that produced it.

## Pre-post checklist

- [x] every placeholder replaced, numbers match `bench/results-longmemeval/test/summary.md`
- [ ] figure regenerated after the final run (`python bench/chart.py`)
- [x] handle and copyright filled in (`ruijiezh67`) across README ×2, LICENSE, `.claude-plugin/*.json`, AGENTS.md — swap the LICENSE line for a legal name if you prefer
- [ ] all three install paths tried in a clean environment
- [ ] first comment ready with the link to `bench/` so the data is one click away
