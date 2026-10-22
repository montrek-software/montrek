#!/bin/bash
set -e

. .venv/bin/activate
# Detect CPU count (not super relevant, but can guide concurrency cap)
CPU_COUNT=$(nproc --all 2>/dev/null || echo 4)
if [[ $CPU_COUNT -gt 32 ]]; then
  CPU_COUNT=32
fi
# WORKER_CONCURRENCY sets the number of tasks a worker runs at once; each
# worker service gets its own (worker.yml maps PARALLEL_WORKER_CONCURRENCY and
# FAST_WORKER_CONCURRENCY to it). QUEUE and POOL default to the service's own.
case "$SERVICE" in
sequential_worker)
  # One task at a time is what the queue is for.
  if [[ -n $WORKER_CONCURRENCY && $WORKER_CONCURRENCY != 1 ]]; then
    echo "WARN: ignoring WORKER_CONCURRENCY=$WORKER_CONCURRENCY for $SERVICE, which runs one task at a time." >&2
  fi
  CONCURRENCY=1
  QUEUE=${QUEUE:-sequential_queue}
  POOL=${POOL:-prefork}
  ;;
parallel_worker)
  CONCURRENCY=${WORKER_CONCURRENCY:-${SET_CONCURRENCY:-4}}
  # The fast queue as well: the fast worker is optional.
  QUEUE=${QUEUE:-parallel_queue,fast_queue}
  POOL=${POOL:-prefork}
  ;;
fast_worker)
  CONCURRENCY=${WORKER_CONCURRENCY:-$((CPU_COUNT * 50))}
  QUEUE=${QUEUE:-fast_queue}
  POOL=${POOL:-gevent}
  ;;
*)
  echo "Unknown service $SERVICE" >&2
  exit 1
  ;;
esac
if ! [[ $CONCURRENCY =~ ^[1-9][0-9]*$ ]]; then
  echo "ERROR: worker concurrency for $SERVICE must be a positive number, got '$CONCURRENCY'." >&2
  exit 1
fi
# Cap to avoid extreme values
MAX_CONCURRENCY=500
if [[ $CONCURRENCY -gt $MAX_CONCURRENCY ]]; then
  CONCURRENCY=$MAX_CONCURRENCY
fi

MAX_TASKS_ARGS=""
if [[ "$POOL" == "prefork" ]]; then
  MAX_TASKS_ARGS="--max-tasks-per-child=5"
  # SIGTERM, as sent on a deploy or restart, starts a cold shutdown after the
  # soft shutdown: running tasks get CELERY_WORKER_SOFT_SHUTDOWN_TIMEOUT to
  # finish, the rest go straight back to the queue (tasks are acknowledged
  # late). A plain warm shutdown waits until SIGKILL, and Redis hands an
  # unacknowledged task out again only after its visibility timeout. Not for
  # gevent: Celery's soft and cold shutdown fail there and lose the task.
  export REMAP_SIGTERM=SIGQUIT
fi

cd montrek
exec python -m celery --app=montrek worker --loglevel=info -Q "$QUEUE" --concurrency="$CONCURRENCY" -n "$SERVICE@%h" --pool="$POOL" $MAX_TASKS_ARGS
