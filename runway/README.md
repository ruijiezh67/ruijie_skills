# runway

**Plan your work around your Claude usage limits, so nothing stops halfway.**

Status: v0 prototype, 2026-10-25. Scripts tested on synthetic fixtures (`bench/test_pace.py`, 10/10). Not yet tested in a live session; no benchmark yet.

## Gap it fills

| Existing | Does | Does not |
|---|---|---|
| Usagebar ($9), ccusage, Claude-Code-Usage-Monitor | show used % and reset times | decide what to do next |
| Desktop "Auto-continue when limits reset", claude-auto-resume scripts | resume a session after a reset | prevent the interruption, or use the lockout time |
| caveman, ponytail | spend fewer tokens per task | order tasks |

runway reads the official status line `rate_limits` field (5-hour and 7-day windows), measures burn rate, and orders the backlog:

- big tasks go into fresh headroom;
- small tasks that can finish go at the end of a window;
- non-model jobs (training, Colab, CI) launch *before* the cap, so they run during the lockout;
- weekly quota left unused near the weekly reset pulls backlog work forward.

## Layout

```
skills/runway/SKILL.md            planning rules and plan format
skills/runway/scripts/snap.py     status line command: records samples to ~/.claude/runway/
skills/runway/scripts/pace.py     tier (GREEN/AMBER/RED/UNKNOWN), burn %/h, hours to cap
skills/runway/references/setup.md settings.json snippet (user applies it)
bench/test_pace.py                deterministic tests, fixture rules in the docstring
```

## Open before v0.1

- Live test: enable the status line, collect a week of samples, check burn-rate estimates against `/usage`.
- Benchmark idea: replay real sample traces with a fixed backlog; compare "tasks interrupted by a limit" and "quota unused at weekly reset" for runway vs. FIFO order.
- Measure per-task cost (Δ used% per task) so sizes come from data, not guesses.
- Pairing with `shift-change`: automatic handover at RED.
