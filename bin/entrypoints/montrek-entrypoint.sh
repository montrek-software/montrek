#!/bin/bash
set -e
echo "SERVICE is: $SERVICE"

/montrek/bin/entrypoints/privileged-entrypoint.sh

# Conditionally run the app as appuser only for the "web" role
echo "Running $SERVICE logic..."
case "$SERVICE" in
web)
  exec gosu "${PUID}:${PGID}" /montrek/bin/entrypoints/web-entrypoint.sh
  ;;
sequential_worker)
  exec gosu "${PUID}:${PGID}" /montrek/bin/entrypoints/worker-entrypoint.sh 1 "$SERVICE"
  ;;
parallel_worker)
  exec gosu "${PUID}:${PGID}" /montrek/bin/entrypoints/worker-entrypoint.sh 5 "$SERVICE"
  ;;
celery_beat)
  exec gosu "${PUID}:${PGID}" /montrek/bin/entrypoints/celery_beat-entrypoint.sh
  ;;
*)
  exec gosu "${PUID}:${PGID}" "$@"
  ;;
esac
