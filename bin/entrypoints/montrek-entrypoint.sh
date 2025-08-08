#!/bin/bash
set -e
echo "SERVICE is: $SERVICE"

# Conditionally run the app as appuser only for the "web" role
if [[ "$SERVICE" == "web" ]]; then
  echo "Running $SERVICE logic..."
  exec /montrek/bin/entrypoints/web-entrypoint.sh
elif [[ "$SERVICE" == "sequential_worker" ]]; then
  echo "Running $SERVICE logic..."
  exec /montrek/bin/entrypoints/worker-entrypoint.sh 1 $SERVICE
elif [[ "$SERVICE" == "parallel_worker" ]]; then
  echo "Running $SERVICE logic..."
  exec /montrek/bin/entrypoints/worker-entrypoint.sh 5 $SERVICE
elif [[ "$SERVICE" == "celery_beat" ]]; then
  echo "Running $SERVICE logic..."
  exec /montrek/bin/entrypoints/celery_beat-entrypoint.sh
else
  echo "Skipping appuser switch for role: $SERVICE"
  exec "$@" # Or run default logic for other services
fi
