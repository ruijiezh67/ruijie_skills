# ruijie_skills

**Agent skills that make an agent's output checkable.** Each one targets a failure we measured in Claude Code, ships a stdlib-only checker script, and comes with deterministic tests and a re-runnable eval.

| skill | what it does | measured |
|---|---|---|
| [**notary**](notary/) | No receipt, no number. Every figure the agent reports points to the file, command output or calculation it came from, and a checker verifies it. Receipts expire when their inputs change. | Stale number reported after a silent re-run: 6/6 with no skill, **0/6** with notary + hooks |
| [**decoy**](decoy/) | Fake data that can't be mistaken for real, and can be made again: reserved values from published standards, a seeded generator, a data card, a linter. | Card numbers that could belong to someone: 600/600 with no skill, **0/600** with decoy |

## Install

Claude Code:

```
/plugin marketplace add ruijiezh67/ruijie_skills
/plugin install notary@ruijie-skills
/plugin install decoy@ruijie-skills
```

Any agent that reads `SKILL.md` files:

```bash
npx skills add https://github.com/ruijiezh67/ruijie_skills/tree/main/notary/skills/notary
npx skills add https://github.com/ruijiezh67/ruijie_skills/tree/main/decoy/skills/decoy
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

Run the tests: `python notary/evals/test_notary.py` and `python decoy/evals/test_decoy.py`.

## How the numbers are made

Every benchmark run is isolated from the operator's own setup (no user CLAUDE.md, skills, plugins or MCP servers). It is scored by regexes against an answer key, never by a model judge, and records the Claude Code version and models used. Where a skill does not help, the README says so: on single-turn summaries the bare model already avoids every trap notary targets.

Both skills are submitted to [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) (`agent_skills/`, PRs [#1270](https://github.com/Shubhamsaboo/awesome-llm-apps/pull/1270) and [#1271](https://github.com/Shubhamsaboo/awesome-llm-apps/pull/1271)).

## Author

Ruijie Zheng ([@ruijiezh67](https://github.com/ruijiezh67)). MIT License.
