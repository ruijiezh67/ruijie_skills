# The exam: a fresh reader reads the handover back

A handover written by the agent that lived the session always looks complete *to that agent*, because it fills the gaps from memory without noticing. The only reliable test is a reader who has none of that memory. That reader is a fresh subagent.

## 1. Write the questions from the session, not from the document

Draft the questions and answer key from the transcript digest and your context **before re-reading the handover**. Questions written from the document only test that the document agrees with itself.

Aim for 8–12 questions. Cover every Tier 1 area that has content, then Tier 2:

| Type | Example | Tests |
|---|---|---|
| Taste choice | "The user asks you to clean up the figure script. Do you refactor it into modules or make the minimal edit? Why?" | taste table |
| No-go zone | "A colleague suggests lowering the learning rate to fix the divergence. What do you say?" | rejected path + reason + reopen condition |
| Next action | "What is the first thing you do, and how do you know it is finished?" | action list |
| Evidence status | "Is it established that the drop comes from tokenization? What is the evidence?" | verified / assumed |
| Mental map | "What is the leading hypothesis for the NaN loss, and what result would kill it?" | open hypotheses |
| Whose view | "What does the user think causes X, and do you (the agent) see it differently?" | the user's view survived the agent writing the handover |
| Running | "Where will the sweep's results appear, and when should you look?" | running jobs |
| Gotcha | "You are about to launch a job on node7. What must you do first?" | traps |
| Jargon | "What does 'the clean set' refer to, exactly?" | glossary |

**Key the user's views from the user's words.** Your answer key shares your blind spots: if you came to believe your own explanation during the session, you will write it into the handover *and* into the key, and the exam will pass while the user's view is lost. So whenever the user stated a hypothesis, a judgement or a preference, include at least one "whose view" question and write its key by quoting the user's messages (the transcript digest lists them), not from your own understanding. If your view and theirs differ, the key is theirs, and the handover must show both.

Good questions have one right answer that the session makes unambiguous, and a wrong answer that a sensible newcomer *would plausibly give*. Prefer scenario phrasing ("the user asks X, what do you do?") over recall ("what does the handover say about X?"). Scenarios test whether the reader can act on the handover, which is the point.

## 2. The examinee prompt

Spawn a new general-purpose subagent with this prompt (fill in the path and questions):

```
You are taking over a project you have never seen. Everything you know must come from
the handover file at <path> and, if needed, files in the repository.
Rules:
- Do NOT read anything under ~/.claude/, any chat logs or transcripts, or other files in .shift/.
- Answer each question in 1–3 sentences.
- If the handover does not tell you, answer exactly "NOT IN HANDOVER". Do not guess:
  a guess hides a gap that someone needs to fix.
Questions:
1. …
```

Run it read-only: it must not edit files or run experiments.

## 3. Grade

For each answer: **correct** (matches the key in substance), **partial** (right direction, missing the reason or the condition), **wrong**, or **gap** ("NOT IN HANDOVER"). Score = number correct. Pass = every Tier 1 question correct and ≥ 80% overall.

## 4. Patch, then re-examine

For each non-correct answer, name the cause before editing:

- **missing**: the fact is not in the handover → add it to the section where it belongs.
- **buried**: it is there, but the reader didn't find it → move it up a tier or make it a table row.
- **ambiguous**: it is there, but it reads two ways → rewrite with the concrete case.
- **contradicted**: two parts disagree → fix the stale one.

Do not append a Q&A section: the real next session won't be asked your questions. Then give a **new** subagent the patched handover and **rephrased** versions of the missed questions (the same fact, a different scenario). At most 2 patch rounds, then stop and list what is still open under "Known gaps".

## 5. Report

Footer line: `Handover fidelity: <correct>/<total> (<k> patch rounds) · Known gaps: …`. Tell the user which categories failed on the first try. That is also a signal about which parts of the work were communicated most poorly during the session itself.
