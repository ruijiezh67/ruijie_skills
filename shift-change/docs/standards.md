# Compliance with the official Agent Skills guidance

Audited 2026-10-01 against Anthropic's documentation and the open Agent Skills specification. Each row is a published rule, not a community convention.

| Rule (source) | Status here |
|---|---|
| `name` and `description` are the only required frontmatter fields ([overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview), [spec](https://agentskills.io/specification)) | ✅ plus one optional `compatibility` on `shift-change` and `shift-recover` |
| `name`: ≤64 chars, lowercase/digits/hyphens, matches the directory, no "claude"/"anthropic" | ✅ all four |
| `description`: ≤1,024 chars, no XML tags, says what it does **and** when to use it | ✅ 641–880 chars |
| **"Always write in third person"** — a mixed point of view "can cause discovery problems" ([best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)) | ✅ fixed 2026-10-01; the descriptions previously opened imperatively ("Hand the current session over…") |
| Descriptions are triggers, not summaries; include the phrases users actually type ([lessons post](https://claude.dev/blog/lessons-from-building-claude-code-how-we-use-skills/)) | ✅ quoted trigger phrases, English and Chinese (no official rule either way on other languages) |
| SKILL.md body under 500 lines / under ~5k tokens ([best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), [Claude Code skills](https://code.claude.com/docs/en/skills)) | ✅ 69–81 lines each |
| `references/` loaded on demand, one level deep, each file focused | ✅ 15–88 lines per file, all linked directly from SKILL.md |
| Table of contents for reference files over 100 lines | ✅ not needed (none exceed 100) |
| Forward slashes in paths, "even on Windows" | ✅ the only backslashes are inside `sanitize.md`, where Windows paths are the thing being detected |
| Variables for the skill's own directory (`${CLAUDE_SKILL_DIR}`) ([plugins reference](https://code.claude.com/docs/en/plugins-reference)) | ✅ fixed 2026-10-01; was an unresolvable `<this-skill-dir>` placeholder |
| Scripts self-contained or dependencies documented; handle their own errors | ✅ `mine_transcript.py`: standard library only, degrades to a message when no transcript exists |
| "The highest-signal content in any skill is the Gotchas section" ([lessons post](https://claude.dev/blog/lessons-from-building-claude-code-how-we-use-skills/)) | ✅ added 2026-10-01 to all four (shift-recover shipped with one) |
| At least three evaluations, tested across models | ⚠️ cases written in [`../evals/README.md`](../evals/README.md); not yet executed (`claude plugin eval` is absent from the installed CLI 2.1.92) |
| "The context window is a public good"; every paragraph must justify its token cost | ✅ handovers point at files instead of pasting them, with a budget of ~200 lines; the transcript digest is capped |
| Plugin manifest validates (`claude plugin validate`) | ✅ passes; two unrecognised root keys (`$schema`, `description`) were removed and `metadata.description` added |
| "Use Skills only from trusted sources"; review `allowed-tools` of skills in a repo | ℹ️ these skills declare no `allowed-tools`, so they inherit the session's permissions; the exam and cold-start steps spawn read-only subagents |

## Deliberate deviations

- **Descriptions are longer than the documentation's "~100 tokens per Skill" figure** (ours are roughly 160–200 tokens each). The cap is 1,024 characters, so this breaks no rule, and the trigger phrases are what make the skills fire on natural phrasing. The honest test is a `claude plugin eval` Δ once the CLI supports it: if the extra phrases don't change triggering, they should go.
- **Chinese trigger phrases**: no official source addresses other languages. They stay because the author and part of the audience type Chinese.
- **Subagents**: endorsed rather than forbidden — "specialized sub-agents can handle focused tasks with clean context windows" ([context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)) — and every step that uses one states what happens when subagents are unavailable.

## Claims we checked and dropped

Widely repeated advice with no official source behind it: a "~200–500 character" description target, a "50–150 line" SKILL.md target, a maximum number of installed skills before degradation, required section headings, and `/skill-doctor` as an official validator (it is third-party). We follow the documented numbers only.
