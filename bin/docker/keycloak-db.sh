#!/bin/bash
if [[ "$1" == "backup" ]]; then
  docker compose exec web bash bin/local/keycloak-db.sh backup
fi
