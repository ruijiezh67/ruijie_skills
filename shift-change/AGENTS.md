# For AI agents installing or using this repo

This repo contains four agent skills in `skills/`: `shift-change`, `shift-start`, `shift-recover`, `shift-brief`.
Each is a folder with a `SKILL.md` (Agent Skills format) plus optional `references/` and `scripts/`.

To install for the user, copy each folder in `skills/` into the user's skills directory:
- Claude Code: `~/.claude/skills/` (all projects) or `<project>/.claude/skills/` (one project)
- Other agents: the agent's skills directory (see its docs), or `npx skills add https://github.com/ruijiezh67/ruijie_skills/tree/main/shift-change/skills`

Then tell the user the four commands: `/shift-change` at the end of a session, `/shift-start` at the start of the next, `/shift-recover` when a session died without a handover, `/shift-brief` to hand a task to someone else.
`scripts/mine_transcript.py` needs Python 3.8+ (standard library only) and only works with Claude Code transcripts; the skills work without it.
