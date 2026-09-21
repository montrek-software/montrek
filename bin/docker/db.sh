#!/bin/bash
# Thin wrapper around bin/local/db.sh inside the web container. Any further
# arguments -- --plain / --binary -- are passed straight through.
COMMAND="$1"
shift 2>/dev/null

if [[ "$COMMAND" == "backup" || "$COMMAND" == "restore" ]]; then
  docker compose exec web bash bin/local/db.sh "$COMMAND" "$@"
else
  echo "Usage: bin/docker/db.sh {backup|restore} [--plain|--binary]" >&2
  exit 1
fi
