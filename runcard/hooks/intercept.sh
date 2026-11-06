#!/usr/bin/env bash
# runcard PreToolUse hook: when a Bash command looks like it will cost real time or money,
# remind the agent to resolve and confirm the settings first (the runcard skill).
#
# Pure pattern matching, no model call, no network. It never blocks: on any problem it exits 0
# silently, because a hook that stops work is a hook that gets uninstalled.
#
# Extend the two pattern lists below; they are the whole configuration.

set -u

# Commands that launch long work.
LAUNCHERS='torchrun|accelerate[[:space:]]+launch|deepspeed|sbatch|srun|qsub|bsub|wandb[[:space:]]+sweep|wandb[[:space:]]+agent|optuna|ray[[:space:]]+(submit|job)|python[0-9.]*[[:space:]]+[^|;]*(train|finetune|fine_tune|pretrain|sweep|eval|evaluate|benchmark|distill)[^|;]*\.py|nohup|tmux[[:space:]]+new-session|screen[[:space:]]+-dm'

# Commands that spend money or are painful to redo.
SPENDERS='modal[[:space:]]+run|sky[[:space:]]+(launch|jobs)|runpodctl|vast[[:space:]]+create|aws[[:space:]]+(batch|sagemaker|ec2[[:space:]]+run-instances)|gcloud[[:space:]]+(batch|ai)|az[[:space:]]+ml|huggingface-cli[[:space:]]+upload|hf[[:space:]]+jobs|docker[[:space:]]+run[^|;]*--gpus'

# Cheap things that match the patterns above but are not worth a card.
EXEMPT='--help|-h$|--dry[-_]?run|--test-only|--validate-only|--check[[:space:]]|--version|pytest|--smoke|echo[[:space:]]|squeue|sacct|scancel|nvidia-smi'

payload=$(cat 2>/dev/null) || exit 0
command=$(printf '%s' "$payload" | python -c "
import json,sys
try:
    d = json.load(sys.stdin)
    print((d.get('tool_input') or {}).get('command', ''))
except Exception:
    pass
" 2>/dev/null) || exit 0

[ -z "$command" ] && exit 0
printf '%s' "$command" | grep -qiE -- "$EXEMPT" && exit 0
printf '%s' "$command" | grep -qiE -- "$LAUNCHERS|$SPENDERS" || exit 0

# One-shot pass: the skill writes the exact command the user confirmed into .runcard/.confirmed.
# Matching is on the full text, so any edit after the confirmation lands back here — that is the
# staleness check. A used line is removed, so one confirmation buys one launch.
CONFIRMED=.runcard/.confirmed
if [ -f "$CONFIRMED" ] && grep -Fxq -- "$command" "$CONFIRMED" 2>/dev/null; then
  grep -Fxv -- "$command" "$CONFIRMED" > "$CONFIRMED.tmp" 2>/dev/null
  mv -f "$CONFIRMED.tmp" "$CONFIRMED" 2>/dev/null   # empty file is fine: nothing is confirmed any more
  exit 0
fi

# Block the call (exit 2) and tell the model why: additionalContext alone does NOT stop the
# command — the tool runs and the note arrives afterwards, which is useless for a launch.
cat >&2 <<'MSG'
Blocked by runcard: this command spends real time or money, and it has not been confirmed yet.

Use the runcard skill first. Resolve every setting the command will actually use by READING the
command line, the config files it loads, the environment and any no-op resolver (--print-config,
--cfg job --resolve, --dryrun). Do not run the entry point to find out. Tag each setting
YOU SAID / INFERRED / DEFAULT / CARRIED / UNKNOWN, check the cross-field risks, show only what
changed since the last confirmed card in .runcard/, and get one confirmation from the user.

Once the user confirms, append the exact command text as a single line to .runcard/.confirmed
and run it unchanged. The line is consumed on use, and any edit to the command after the
confirmation brings you back here.
MSG
exit 2
