---
name: runway
description: >
  Orders a task backlog against the remaining Claude usage quota so work never
  stops mid-task at a limit. Reads the live 5-hour and weekly rate-limit windows,
  measures burn rate, then schedules heavy tasks into fresh headroom, finishable
  small tasks into the tail of a window, and long non-model jobs (training,
  cloud runs, CI, waiting on people) right before a cap so they run during the
  lockout. Use when the user says "runway", "plan around my limits", "how much
  quota is left", "what should I do before the limit", "schedule my tasks", or lists several tasks for a long
  session or overnight.
argument-hint: "[task list | status]"
license: MIT
---

# Runway

Quota is fuel. Never take off on a leg you cannot land: a task that hits the
limit halfway costs its tokens twice, once to do it and once to rebuild the
context afterwards.

## 1. Read the gauges (always first)

Run `python <skill-dir>/scripts/pace.py`. It prints a tier and both windows:
used %, time to reset, burn rate in %/hour, hours until cap.

- `UNKNOWN` or "no samples": the status line recorder is not set up. Give the
  user the setup from `references/setup.md` and plan from `/usage` numbers they
  paste. Do not guess quota.
- A value printed `N/A` is unmeasured. Say so. Never treat it as 0.

## 2. Size every task

For each task in the backlog, write one row: task, kind, size, needs-model.

- **kind**: `model` (Claude does the work), `wall` (runs without Claude: a
  training job, Colab, CI, a sweep, a reviewer replying), or `mixed`.
- **size** in % of a 5-hour window: S under 5, M 5 to 20, L over 20. Estimate
  from the measured burn rate times expected active hours. If there is no
  burn rate yet, say the size is a guess.
- **interruptible**: can it stop halfway with a usable checkpoint?

## 3. Order by these rules

Apply in order. The ones above win.

1. **Start an L task only if headroom covers it with a 30% margin**
   (`100 - used ≥ 1.3 × size`). Otherwise schedule it as the first thing
   after the next reset.
2. **Launch `wall` jobs before the cap, not after.** At AMBER or RED, the most
   valuable thing left is starting work that runs while Claude is locked out.
   Prepare them first (configs checked, outputs separated) so they launch clean.
3. **Fill the tail of a window with S tasks that finish.** Reviews, docs,
   small fixes, writing up results.
4. **Weekly pace beats the 5-hour window.** If `pace.py` says weekly use is
   ahead of even pace, defer optional L tasks to after the weekly reset. If the
   weekly reset is under 48 h away with quota unused, pull L tasks forward:
   unused quota does not carry over.
5. **At RED, land the plane.** Finish or checkpoint the current task. If the
   `shift-change` skill is installed, run it so the next window resumes with
   full context. Tell the user that Desktop's "Auto-continue when limits
   reset" checkbox (on the session-limit card, not the weekly one) resumes
   the turn after the reset.
6. At AMBER, route S tasks and searches to a lighter model, then check on the
   next `pace.py` reading that the burn rate actually fell. Do not assume it.

## 4. Show the plan, ask once

```
## Runway  5h 62% (↻1h40m, 18%/h → cap in 2.1h) · 7d 48% (pace 0.9x) · AMBER

  #  when          task                         kind   size  why
  1  now           launch sweep on Colab        wall   S     runs through lockout
  2  now           fix test flake               model  S     finishes in window
  3  now           write results section        model  M     fits: 38% left ≥ 1.3×20
  4  after ↻1h40m  refactor data loader         model  L     needs 35%, have 38%, margin too thin
  5  at 90%        /shift-change                —      S     next window starts warm

  Go · Reorder · Change a size
```

Then work the plan. Re-run `pace.py` between tasks, not just once: burn rate
changes with the work. If a new reading changes the plan, show only what
changed.

## Rules

- Quota numbers come from `pace.py` or `/usage`. Never from memory, blog posts
  or plan names: Anthropic no longer publishes fixed limits.
- Do not pad work to use up quota. The weekly rule pulls real backlog forward;
  it does not invent tasks.
- Do not suggest more accounts, shared seats or other ways around the limits.
