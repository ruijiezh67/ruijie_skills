# Launch plan

What actually made the reference repos grow (see `_learning/skill-anatomy.md`): a name that is also the trigger phrase, a change in behaviour you can show in 20 seconds, evidence nobody else bothered to produce, and an author who keeps answering. Nothing here works without the first two.

## 0. Assets to have before anything is posted

| Asset | State | Note |
|---|---|---|
| One-sentence pitch | ready | "Hospitals cut handoff errors 23% with one rule: the incoming nurse reads the handoff back. `shift-change` gives your coding agent the same rule." |
| Demo GIF, 20–30 s | **todo** | the exam failing then passing: `5/12 → patched → 12/12`. This is the whole product in one image. |
| Benchmark table | ready (synthetic) + running (LongMemEval) | publish raw outputs, including the runs we lost |
| Feature comparison | ready | `docs/comparison.md` |
| README (English) | ready | handle `ruijiezh67` filled in; LICENSE says `ruijiezh67`, swap for a legal name if preferred |
| Install paths tested | **todo** | plugin marketplace, `npx skills add`, git clone, "paste the link to your agent" |
| CHANGELOG as a story | ready | every rule traces to a failure; this is what makes the repo feel earned |

## 1. Seed week (before any public post)

- Use it daily on your own research. Every time the next session still misses something, that is a CHANGELOG entry.
- Give it to 3–5 labmates. Ask one question: *what did the new session still not know?*
- Collect two concrete before/after stories with real numbers. One of them becomes the demo.
- Fix the single most common complaint. Ignore the rest until launch.

## 2. Launch day

**The post that spreads is not "I made a skill". It is a finding.** You have one: *we benchmarked eight handoff skills against Claude Code's own `/compact` on an academic memory benchmark, and published the raw data*. Lead with the finding; the skill is how the finding was produced.

X thread, six posts:
1. Hook: the hospital number, then the one-line claim. Attach the demo GIF.
2. The benchmark table as an image, with the honest caveat in the same post (lead within one SD; `/compact` is strong).
3. The one failure story: the handover that said "root cause located" while the mental map still listed it as an open hypothesis.
4. What it does that others don't: reads the raw transcript (pre-compaction corrections), records taste as rules, tests itself on a fresh agent.
5. Install: the one-liner, plus "or send the repo link to your agent".
6. The limits, in your own words: handover is compression; for arbitrary details, reading the full history still wins. People trust a project that says this.

Same day, no extra effort:
- **skills.sh**: `npx skills add <user>/shift-change` should work; add the badge to the README.
- **Plugin marketplace**: `/plugin marketplace add <repo url>`.
- **Awesome lists**: PRs to `hesreallyhim/awesome-claude-code`, `ComposioHQ/awesome-claude-skills`, `travisvn/awesome-claude-skills`. One PR each, linking the benchmark.
- **Reddit r/ClaudeAI** and the Claude Discord: post the benchmark, not the pitch.
- Reply to every comment for the first 48 hours. This is the highest-leverage work of the whole launch.

## 3. Weeks 1–4

- **Fix and ship fast.** An issue answered within a day converts a user into someone who tells others.
- **Milestone posts** at 1k / 5k / 10k stars: each one is a chance to restate the pitch to people who missed it.
- **A "how I built it" long post.** Your angle is unusual and worth telling plainly: a researcher, working with an agent, built a skill *and* an adversarial benchmark against eight competitors, and published the runs where the skill lost.
- **A YouTube walkthrough** of one real session: work, `/shift-change`, new session, `/shift-start`, watch it read back.
- **Extract a second skill** from the same repo once people ask for it (`cold-start` is the obvious one: the exam engine, for any README or protocol).

## 4. Things that lose trust

- Rounding the benchmark in your favour, or dropping the conditions where you lose.
- Claiming what the data doesn't support (we removed one such claim already: see CHANGELOG).
- Star-for-star trades, tag-bombing, engagement farming.
- Going quiet for a week after launch.

## 5. What to measure

Installs on skills.sh, stars per day after each post, issues opened and time to first reply, and how many of the issues come from people who are not in your lab. The last number is the real one.
