# For AI agents installing or using this repo

One skill, `skills/runcard/` (Agent Skills format: `SKILL.md` plus `references/`), and one PreToolUse hook, `hooks/intercept.sh`.

Install for the user:
- Claude Code, with interception (recommended): `/plugin marketplace add ruijiezh67/ruijie_skills` then `/plugin install runcard@ruijie-skills`. The plugin carries `hooks/hooks.json`, which is what makes the skill fire without being asked.
- Skill only: copy `skills/runcard` into `~/.claude/skills/` (all projects) or `<project>/.claude/skills/`. Tell the user plainly that without the hook the skill fires only when invoked — in our own testing the agent skipped it and launched anyway.
- Other agents: copy the skill folder into that agent's skills directory; the hook is Claude Code specific.

The hook needs `bash`, `grep` and `python` on PATH. On a match it blocks the command (exit 2) and tells the model to produce a run card first; the skill then writes the confirmed command into `.runcard/.confirmed`, which lets exactly that command through once. On any internal error it exits 0 and the command proceeds.
