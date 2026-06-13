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

  echo "$KEYCLOAK_DB_HOST:$KEYCLOAK_DB_PORT:$KEYCLOAK_DB_NAME:$KEYCLOAK_DB_USER:$KEYCLOAK_DB_PASSWORD" >~/.pgpass
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
fi
