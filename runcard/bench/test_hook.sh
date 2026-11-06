#!/usr/bin/env bash
# Pattern tests for hooks/intercept.sh. No model, no network: runs in under a second.
#   bash bench/test_hook.sh
# A case is "intercept" if the hook emits JSON, "pass" if it stays silent.

cd "$(dirname "$0")/.." || exit 1
HOOK=hooks/intercept.sh
fail=0

check() { # check <expected: intercept|pass> <command>
  local expected=$1 cmd=$2 got
  printf '{"tool_input":{"command":%s}}' \
    "$(python -c "import json,sys;print(json.dumps(sys.argv[1]))" "$cmd")" | bash "$HOOK" >/dev/null 2>&1
  [ $? -eq 2 ] && got=intercept || got=pass   # exit 2 blocks the tool call, 0 lets it through
  if [ "$got" = "$expected" ]; then
    printf '  ok    %-9s %s\n' "$got" "$cmd"
  else
    printf '  FAIL  expected %-9s got %-9s %s\n' "$expected" "$got" "$cmd"; fail=$((fail + 1))
  fi
}

echo "costly commands (must intercept):"
check intercept "torchrun --nproc_per_node 4 train.py --config configs/clip.yaml"
check intercept "accelerate launch finetune.py"
check intercept "deepspeed train.py --deepspeed ds.json"
check intercept "sbatch scripts/train.sbatch"
check intercept "srun --gres=gpu:1 python main.py"
check intercept "wandb sweep sweep.yaml"
check intercept "python train.py --lr 3e-5"
check intercept "python3 scripts/finetune_lora.py"
check intercept "nohup python sweep.py &"
check intercept "modal run train_modal.py"
check intercept "sky launch -c dev task.yaml"
check intercept "docker run --gpus all myimg python train.py"

echo "cheap or read-only (must pass):"
check pass "python analyse_results.py"
check pass "python train.py --help"
check pass "sbatch --test-only scripts/train.sbatch"
check pass "sky launch --dryrun task.yaml"
check pass "pytest tests/"
check pass "squeue -u \$USER"
check pass "sacct -j 481516"
check pass "nvidia-smi"
check pass "git status"
check pass "ls runs/"
check pass "cat configs/clip.yaml"

echo "malformed input (must fail open, silently):"
printf 'not json' | bash "$HOOK" >/dev/null 2>&1
[ $? -eq 0 ] && echo "  ok    pass      <garbage stdin>" || { echo "  FAIL  blocked on garbage input"; fail=$((fail + 1)); }
printf '{"tool_input":{}}' | bash "$HOOK" >/dev/null 2>&1
[ $? -eq 0 ] && echo "  ok    pass      <empty command>" || { echo "  FAIL  blocked on empty command"; fail=$((fail + 1)); }

echo "confirmed command passes once, then blocks again:"
tmp=$(mktemp -d); mkdir -p "$tmp/.runcard"; printf 'python train.py --run_name=x
' > "$tmp/.runcard/.confirmed"
( cd "$tmp" && printf '{"tool_input":{"command":"python train.py --run_name=x"}}' | bash "$OLDPWD/$HOOK" >/dev/null 2>&1; [ $? -eq 0 ] && echo "  ok    pass      confirmed line lets the command through" || { echo "  FAIL  confirmed line was blocked"; exit 1; } )
[ $? -ne 0 ] && fail=$((fail + 1))
( cd "$tmp" && printf '{"tool_input":{"command":"python train.py --run_name=x"}}' | bash "$OLDPWD/$HOOK" >/dev/null 2>&1; [ $? -eq 2 ] && echo "  ok    intercept same command a second time (one-shot)" || { echo "  FAIL  confirmation was not consumed"; exit 1; } )
[ $? -ne 0 ] && fail=$((fail + 1))
rm -rf "$tmp"

echo
[ "$fail" -eq 0 ] && echo "all cases passed" || echo "$fail case(s) failed"
exit "$fail"
