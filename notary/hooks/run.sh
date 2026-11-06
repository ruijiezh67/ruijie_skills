#!/bin/sh
# Pick a Python that actually runs (python3 can be a Windows Store stub), then hand over stdin.
here=$(dirname "$0")
script="$here/../skills/notary/scripts/notary.py"
for py in python3 python; do
  if "$py" -c "import sys; sys.exit(sys.version_info < (3, 8))" >/dev/null 2>&1; then
    exec "$py" "$script" "$@"
  fi
done
exit 0  # no Python: fail open
