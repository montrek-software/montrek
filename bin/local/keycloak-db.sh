#!/bin/bash

# Backup and restore the keycloak database. The work is in
# bin/lib/db-backup.sh, which this shares with db.sh; see there for the
# formats and the retention rules.
#
#   keycloak-db.sh backup [--plain]     # binary by default, SQL text with --plain
#   keycloak-db.sh restore [--plain|--binary]

# Configuration comes from the environment first and only then from .env, so
# this works unchanged on the host and inside a container where .env is
# deliberately shadowed.
# shellcheck source=../lib/load-env.sh
. "$(dirname "${BASH_SOURCE[0]}")/../lib/load-env.sh"
montrek_load_env
# shellcheck source=../lib/db-backup.sh
. "$(dirname "${BASH_SOURCE[0]}")/../lib/db-backup.sh"

montrek_require_env KEYCLOAK_DB_PASSWORD || exit 1

MONTREK_DB_LABEL="keycloak database"
MONTREK_DB_PREFIX="keycloak_backup"
MONTREK_DB_HOST="${KEYCLOAK_DB_HOST:-keycloak-db}"
MONTREK_DB_PORT="${KEYCLOAK_DB_PORT:-5432}"
MONTREK_DB_NAME="${KEYCLOAK_DB_NAME:-keycloak}"
MONTREK_DB_USER="${KEYCLOAK_DB_USER:-keycloak}"
MONTREK_DB_PASSWORD="$KEYCLOAK_DB_PASSWORD"

montrek_db_parse_args "$@" || exit 1

echo "Environment variables loaded successfully."
echo "Keycloak DB Host: $MONTREK_DB_HOST"
echo "Keycloak DB Name: $MONTREK_DB_NAME"
echo "Keycloak DB User: $MONTREK_DB_USER"
echo "Days to keep: $DB_BACKUP_KEEP_DAYS"

montrek_db_dispatch
