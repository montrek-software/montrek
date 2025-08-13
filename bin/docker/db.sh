#!/bin/bash
if [[ "$1" == "backup" ]]; then
  docker compose exec web bash bin/local/db.sh backup
elif [[ "$1" == "restore" ]]; then
  docker compose exec web bash bin/local/db.sh restore
fi
