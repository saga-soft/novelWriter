#!/bin/bash

# A debug script that will run the test suite repeatedly, looking for
# crashes. Takes the number of attempts as $1 (default 10). Any further
# arguments are forwarded to pytest, e.g. --run-long.

COUNT=${1:-10}
shift || true

mkdir -p ./debug
LOGDIR=./debug
i=0
while [ $i -lt "$COUNT" ]; do
  i=$((i + 1))
  echo "=== Attempt $i ($(date '+%H:%M:%S')) ==="
  QT_QPA_PLATFORM=offscreen gdb --batch \
    -ex "handle SIGSEGV stop nopass" \
    -ex "handle SIGABRT stop nopass" \
    -ex run -ex "bt full" -ex quit \
    --args .venv/bin/python -m pytest tests -q "$@" \
    > "$LOGDIR/crash_hunt_run_$i.log" 2>&1
  if grep -qE "SIGSEGV|SIGABRT|Segmentation fault" "$LOGDIR/crash_hunt_run_$i.log"; then
    echo ">>> CRASH on attempt $i — see $LOGDIR/crash_hunt_run_$i.log <<<"
    break
  fi
  rm -f "$LOGDIR/crash_hunt_run_$i.log"
done
echo "Stopped after $i/$COUNT attempt(s), $((SECONDS / 60)) min elapsed."
