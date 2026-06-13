#!/bin/bash

# Load variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found!"
  exit 1
fi

# Check if required variables are set
if [[ -z "$KEYCLOAK_DB_PASSWORD" ]]; then
  echo "KEYCLOAK_DB_PASSWORD is missing in .env"
  exit 1
fi

KEYCLOAK_DB_HOST="${KEYCLOAK_DB_HOST:-keycloak-db}"
KEYCLOAK_DB_PORT="${KEYCLOAK_DB_PORT:-5432}"
KEYCLOAK_DB_NAME="${KEYCLOAK_DB_NAME:-keycloak}"
KEYCLOAK_DB_USER="${KEYCLOAK_DB_USER:-keycloak}"

# Set default for DB_BACKUP_KEEP_DAYS if not provided
: "${DB_BACKUP_KEEP_DAYS:=30}"

echo "Environment variables loaded successfully."
echo "Keycloak DB Host: $KEYCLOAK_DB_HOST"
echo "Keycloak DB Name: $KEYCLOAK_DB_NAME"
echo "Keycloak DB User: $KEYCLOAK_DB_USER"
echo "Days to keep: $DB_BACKUP_KEEP_DAYS"

if [[ "$1" == "backup" ]]; then
  BACKUP_FOLDER=db_backups
  DATE=$(date +"%Y-%m-%d_%H-%M-%S")
  BACKUP_FILE="$BACKUP_FOLDER/keycloak_backup_${DATE}.sql"

  # Ensure the backup folder exists
  mkdir -p "$BACKUP_FOLDER"

  echo "$KEYCLOAK_DB_HOST:$KEYCLOAK_DB_PORT:*:$KEYCLOAK_DB_USER:$KEYCLOAK_DB_PASSWORD" >~/.pgpass
  chmod 600 ~/.pgpass

  # Run the pg_dump command inside the Docker container
  pg_dump -U "$KEYCLOAK_DB_USER" -h "$KEYCLOAK_DB_HOST" -d "$KEYCLOAK_DB_NAME" -p "$KEYCLOAK_DB_PORT" >"$BACKUP_FILE"

  # Check if the backup was successful
  if [ $? -eq 0 ]; then
    echo "Backup successful! File: $BACKUP_FILE"
  else
    echo "Backup failed!"
    exit 1
  fi

  # Cleanup logic: remove files older than 1 year and remove files older than 1 month except the last file of the month
  find "$BACKUP_FOLDER" -type f -name "keycloak_backup_*.sql" -mtime +365 -exec rm {} \; # Remove files older than 1 year

  # Find files older than 1 month
  find "$BACKUP_FOLDER" -type f -name "keycloak_backup_*.sql" -mtime +$DB_BACKUP_KEEP_DAYS | while read FILE; do
    # Extract the file creation date
    FILE_DATE=$(basename "$FILE" | sed -E 's/^keycloak_backup_([0-9]{4}-[0-9]{2}-[0-9]{2}).*/\1/')

    # Extract the year, month, and day
    YEAR=$(echo "$FILE_DATE" | cut -d'-' -f1)
    MONTH=$(echo "$FILE_DATE" | cut -d'-' -f2)
    DAY=$(echo "$FILE_DATE" | cut -d'-' -f3)

    # Check if it's the last day of the month
    LAST_DAY=$(date -d "$YEAR-$MONTH-01 +1 month -1 day" +"%d")

    if [ "$DAY" != "$LAST_DAY" ]; then
      echo "Removing file: $FILE (Not the last day of the month)"
      rm "$FILE"
    fi
  done

elif [[ "$1" == "restore" ]]; then
  BACKUP_FOLDER=db_backups

  # Ask the user for the date (format: YYYY-MM-DD)
  read -p "Enter the date of the keycloak backup to restore (format: YYYY-MM-DD): " RESTORE_DATE

  # Check if the user input matches the expected format (YYYY-MM-DD)
  if ! [[ $RESTORE_DATE =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "Invalid date format. Please use YYYY-MM-DD."
    exit 0
  fi

  # Find all matching backup files and pick the latest one by modification time
  BACKUP_FILE=$(find "$BACKUP_FOLDER" -type f -name "keycloak_backup_${RESTORE_DATE}_*.sql" -print0 |
    xargs -0 ls -t 2>/dev/null | head -n 1)

  # Check if a backup file was found
  if [ -z "$BACKUP_FILE" ]; then
    echo "No keycloak backup file found for date: $RESTORE_DATE"
    exit 0
  fi

  # Confirm the restoration
  read -p "Are you sure you want to restore the keycloak database from $BACKUP_FILE? (y/n): " CONFIRM

  if [[ $CONFIRM != "y" ]]; then
    echo "Restore operation cancelled."
    exit 1
  fi

  echo "$KEYCLOAK_DB_HOST:$KEYCLOAK_DB_PORT:*:$KEYCLOAK_DB_USER:$KEYCLOAK_DB_PASSWORD" >~/.pgpass
  chmod 600 ~/.pgpass

  echo "Checking for active connections to $KEYCLOAK_DB_NAME..."

  # Get count of active connections
  ACTIVE_COUNT=$(psql -U "$KEYCLOAK_DB_USER" -d postgres -h "$KEYCLOAK_DB_HOST" -p "$KEYCLOAK_DB_PORT" -t -c "
  SELECT count(*) FROM pg_stat_activity WHERE datname = '${KEYCLOAK_DB_NAME}' AND pid <> pg_backend_pid();
  " | xargs)

  if [ "$ACTIVE_COUNT" -gt 0 ]; then
    echo ""
    echo "⚠️  There are currently $ACTIVE_COUNT active connection(s) to $KEYCLOAK_DB_NAME:"
    echo ""

    # Show details of active connections
    psql -U "$KEYCLOAK_DB_USER" -d postgres -h "$KEYCLOAK_DB_HOST" -p "$KEYCLOAK_DB_PORT" -c "
    SELECT pid, usename AS user, application_name, client_addr, state, query
    FROM pg_stat_activity
    WHERE datname = '${KEYCLOAK_DB_NAME}' AND pid <> pg_backend_pid();
    "

    echo ""
    read -p "Do you want to terminate all these connections? [y/N]: " CONFIRM

    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
      echo "Aborting. Keycloak database restore cancelled."
      exit 1
    fi

    echo "Terminating all active connections..."
    psql -U "$KEYCLOAK_DB_USER" -d postgres -h "$KEYCLOAK_DB_HOST" -p "$KEYCLOAK_DB_PORT" -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '${KEYCLOAK_DB_NAME}' AND pid <> pg_backend_pid();
    "
  else
    echo "No active connections found. Proceeding..."
  fi

  echo ""
  echo "Dropping and recreating the keycloak database..."

  psql -U "$KEYCLOAK_DB_USER" -d postgres -h "$KEYCLOAK_DB_HOST" -p "$KEYCLOAK_DB_PORT" -c "DROP DATABASE IF EXISTS $KEYCLOAK_DB_NAME;"
  psql -U "$KEYCLOAK_DB_USER" -d postgres -h "$KEYCLOAK_DB_HOST" -p "$KEYCLOAK_DB_PORT" -c "CREATE DATABASE $KEYCLOAK_DB_NAME;"

  echo "Restoring the keycloak database from backup..."
  cat "$BACKUP_FILE" | psql -U "$KEYCLOAK_DB_USER" -h "$KEYCLOAK_DB_HOST" -d "$KEYCLOAK_DB_NAME" -p "$KEYCLOAK_DB_PORT"

  if [ $? -eq 0 ]; then
    echo "✅ Keycloak database restored successfully from backup: $BACKUP_FILE"
  else
    echo "❌ Keycloak database restore failed!"
    exit 1
  fi
fi
