#!/bin/bash

# Backup and restore the application database. The work is in
# bin/lib/db-backup.sh, which this shares with keycloak-db.sh; see there for
# the formats and the retention rules.
#
#   db.sh backup [--plain]     # binary by default, SQL text with --plain
#   db.sh restore [--plain|--binary]

# Configuration comes from the environment first and only then from .env, so
# this works unchanged on the host and inside a container where .env is
# deliberately shadowed.
# shellcheck source=../lib/load-env.sh
. "$(dirname "${BASH_SOURCE[0]}")/../lib/load-env.sh"
montrek_load_env
# shellcheck source=../lib/db-backup.sh
. "$(dirname "${BASH_SOURCE[0]}")/../lib/db-backup.sh"

montrek_require_env DB_ENGINE DB_NAME DB_USER DB_PASSWORD DB_HOST DB_PORT || exit 1

MONTREK_DB_LABEL="database"
MONTREK_DB_PREFIX="backup"
MONTREK_DB_HOST="$DB_HOST"
MONTREK_DB_PORT="$DB_PORT"
MONTREK_DB_NAME="$DB_NAME"
MONTREK_DB_USER="$DB_USER"
MONTREK_DB_PASSWORD="$DB_PASSWORD"

montrek_db_parse_args "$@" || exit 1

echo "Environment variables loaded successfully."
echo "DB Engine: $DB_ENGINE"
echo "DB Name: $DB_NAME"
echo "DB User: $DB_USER"
echo "DB Host: $DB_HOST"
echo "DB Port: $DB_PORT"
echo "Days to keep $DB_BACKUP_KEEP_DAYS"

montrek_db_dispatch
