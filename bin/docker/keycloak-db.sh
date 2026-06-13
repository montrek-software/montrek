#!/bin/bash
if [[ "$1" == "backup" ]]; then
  docker compose exec web bash bin/local/keycloak-db.sh backup
elif [[ "$1" == "restore" ]]; then
  docker compose exec web bash bin/local/keycloak-db.sh restore
fi
