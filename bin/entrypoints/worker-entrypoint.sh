#!/bin/bash
set -e

. .venv/bin/activate
# Detect CPU count (not super relevant, but can guide concurrency cap)
CPU_COUNT=$(nproc --all 2>/dev/null || echo 4)
if [[ $CPU_COUNT -gt 32 ]]; then
  CPU_COUNT=32
fi
case "$SERVICE" in
sequential_worker)
  CONCURRENCY=1
  ;;
parallel_worker)
  CONCURRENCY=$((CPU_COUNT - 2))
  ;;
fast_worker)
  CONCURRENCY=$((CPU_COUNT * 50))
  ;;
*)
  echo "Unknown service $SERVICE"
  ;;
esac
# Cap to avoid extreme values
MAX_CONCURRENCY=500
if [[ $CONCURRENCY -gt $MAX_CONCURRENCY ]]; then
  CONCURRENCY=$MAX_CONCURRENCY
fi
if [[ $SET_CONCURRENCY ]]; then
  CONCURRENCY=$SET_CONCURRENCY
fi

cd montrek
python -m celery --app=montrek worker --loglevel=info -Q $QUEUE --concurrency=$CONCURRENCY -n $SERVICE@%h --pool=$POOL
