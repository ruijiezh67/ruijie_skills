# ruijie_skills

**Agent skills that make an agent's work checkable.** Each one targets a failure in how coding agents report, fabricate, hand over or launch work. The skills ship stdlib-only scripts and deterministic tests, and every number in this repo says how and when it was measured, including the ones that no longer hold.

| skill | what it does | status |
|---|---|---|
| [**notary**](notary/) | No receipt, no number. Every figure the agent reports points to the file, command output or calculation it came from, and a checker verifies it. Receipts expire when their inputs change. | v0.2.0. Stale number reported after a silent re-run: 6/6 with no skill, **0/6** with notary + hooks |
| [**decoy**](decoy/) | Fake data that can't be mistaken for real, and can be made again: reserved values from published standards, a seeded generator, a data card, a linter. | v0.2.0. Card numbers that could belong to someone: 600/600 with no skill, **0/600** with decoy |
| [**shift-change**](shift-change/) | Handovers that carry the soul of the work (taste, rejected paths, what's still running), proved by quizzing a fresh agent before you close the session. Four skills: shift-change, shift-start, shift-recover, shift-brief. | v0.1. On LongMemEval (isolated re-run) it ties Claude Code's `/compact` at 20/21; the taste and rejected-path benchmark is pending a re-run |
| [**runcard**](runcard/) | Before a training run, a sweep or any costly command, shows every setting it will truly use and where each came from, flags quietly wrong combinations, and asks once. | v0.1. Headline result does not hold on the current model; needs a harder scenario |
| [**runway**](runway/) | Plans your work around Claude usage limits: heavy tasks into fresh headroom, long non-model jobs into the lockout. | v0 prototype, tested on fixtures only |

## Install

Claude Code:

```
/plugin marketplace add ruijiezh67/ruijie_skills
/plugin install notary@ruijie-skills
/plugin install decoy@ruijie-skills
/plugin install shift-change@ruijie-skills
/plugin install runcard@ruijie-skills
/plugin install runway@ruijie-skills
```

Any agent that reads `SKILL.md` files:

```bash
npx skills add https://github.com/ruijiezh67/ruijie_skills/tree/main/notary/skills/notary
npx skills add https://github.com/ruijiezh67/ruijie_skills/tree/main/decoy/skills/decoy
npx skills add https://github.com/ruijiezh67/ruijie_skills/tree/main/shift-change/skills
```

## Layout

```
.claude-plugin/marketplace.json   one marketplace, one plugin per folder
<skill>/
  skills/<skill>/SKILL.md         the skill, plus scripts/ (Python standard library only)
  hooks/                          optional Claude Code hooks (notary)
  evals/                          deterministic tests; evals/drift/ re-runs the notary benchmark
  bench/                          original benchmark fixtures and raw results
  README.md  CHANGELOG.md
```

Run the tests: `python notary/evals/test_notary.py`, `python decoy/evals/test_decoy.py`, `python runway/bench/test_pace.py`.

## How the numbers are made

Every benchmark run is isolated from the operator's own setup (no user CLAUDE.md, skills, plugins or MCP servers). It is scored by regexes against an answer key, never by a model judge, and records the Claude Code version and models used. Where a skill does not help, the README says so: on single-turn summaries the bare model already avoids every trap notary targets.

Both skills are submitted to [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) (`agent_skills/`, PRs [#1270](https://github.com/Shubhamsaboo/awesome-llm-apps/pull/1270) and [#1271](https://github.com/Shubhamsaboo/awesome-llm-apps/pull/1271)).

## Author

Ruijie Zheng ([@ruijiezh67](https://github.com/ruijiezh67)). MIT License.
