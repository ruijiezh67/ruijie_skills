# How shift-change compares

Popular open-source handoff skills and commands, read from their source on 2026-09-18. Stars are for the containing repo.

| | mattpocock `handoff` | ykdojo `handoff` | humanlayer `create_handoff` | softaworks `session-handoff` | willseltzer `create` | REMvisual `handoff` | **shift-change** |
|---|---|---|---|---|---|---|---|
| Repo stars | ~265k | ~10k | ~11.6k | ~2.5k | 144 | 53 | new |
| Size of the instructions | 16 lines | 18 lines | 95 lines | 189 lines + scripts | 141 lines | 224 lines + refs | 61 lines + refs + script |
| Where the facts come from | agent's context | agent's context | agent's context | agent's context | agent's context | agent's context (multi-pass) | **raw transcript (incl. pre-compaction) + git + live job check + context** |
| Failed / rejected paths | – | "what didn't work" | "learnings" | ✓ | ✓ mandatory | ✓ with rejected alternatives | ✓ with reason **and reopen condition** |
| User preferences / taste | – | – | – | – | a line in context gathering | a checklist item | **rule table: assumed → corrected → rule → user's words** |
| Verified vs assumed | – | – | – | – | – | evidence section | **every claim tagged** |
| Running jobs, gotchas, jargon | – | – | – | partial | warnings, setup | discoveries & gotchas | ✓ dedicated sections |
| Quality check | – | – | – | script: placeholders, secrets, 0–100 score | – | self-validation checklist | **fresh-agent exam + patch rounds, fidelity score** |
| Receiving side | – | "start with the path" | `/resume_handoff` | resume + staleness check | `/resume` | chain detection | `/shift-start`: world check, **readback, waits for OK** |
| Durable taste to memory | – | – | – | – | – | optional memory tool | proposed for CLAUDE.md, **user approves** |
| Hand to a person (files, sanitize, test) | redacts secrets | – | – | secret check | – | – | `/shift-brief`: dependency trace, sanitize, runnable acceptance, **cold-start test** |

What everyone else validates is the *form* of the document (sections present, no placeholders, no secrets). `shift-change` validates the *effect*: whether a reader with no memory of the session can act the way the session would have.

Measured results for the same conditions are in [`../bench/`](../bench/).
