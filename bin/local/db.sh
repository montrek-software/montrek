#!/bin/bash

# Load variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found!"
  exit 1
fi

# Check if required variables are set
if [[ -z "$DB_ENGINE" || -z "$DB_NAME" || -z "$DB_USER" || -z "$DB_PASSWORD" || -z "$DB_HOST" || -z "$DB_PORT" ]]; then
  echo "One or more required environment variables are missing in .env:"
  echo "DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT"
  exit 1
fi
# Set default for DB_BACKUP_KEEP_DAYS if not provided
: "${DB_BACKUP_KEEP_DAYS:=30}"

echo "Environment variables loaded successfully."
echo "DB Engine: $DB_ENGINE"
echo "DB Name: $DB_NAME"
echo "DB User: $DB_USER"
echo "DB Host: $DB_HOST"
echo "DB Port: $DB_PORT"
echo "Days to keep $DB_BACKUP_KEEP_DAYS"

if [[ "$1" == "backup" ]]; then
  BACKUP_FOLDER=db_backups
  DATE=$(date +"%Y-%m-%d_%H-%M-%S")
  BACKUP_FILE="$BACKUP_FOLDER/backup_$DB_NAME_$DATE.sql"

  # Ensure the backup folder exists
  mkdir -p "$BACKUP_FOLDER"

  echo "$DB_HOST:$DB_PORT:$DB_NAME:$DB_USER:$DB_PASSWORD" >~/.pgpass
  chmod 600 ~/.pgpass

  # Run the pg_dump command inside the Docker container
  pg_dump -U $DB_USER -h $DB_HOST -d $DB_NAME -p $DB_PORT >"$BACKUP_FILE"

  # Check if the backup was successful
  if [ $? -eq 0 ]; then
    echo "Backup successful! File: $BACKUP_FILE"
  else
    echo "Backup failed!"
    exit 1
  fi

  # Cleanup logic: remove files older than 1 year and remove files older than 1 month except the last file of the month
  find "$BACKUP_FOLDER" -type f -name "*.sql" -mtime +365 -exec rm {} \; # Remove files older than 1 year

  # Find files older than 1 month
  find "$BACKUP_FOLDER" -type f -name "*.sql" -mtime +$DB_BACKUP_KEEP_DAYS | while read FILE; do
    # Extract the file creation date
    FILE_DATE=$(basename "$FILE" | cut -d'_' -f2)

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
  read -p "Enter the date of the backup to restore (format: YYYY-MM-DD): " RESTORE_DATE

  # Check if the user input matches the expected format (YYYY-MM-DD)
  if ! [[ $RESTORE_DATE =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "Invalid date format. Please use YYYY-MM-DD."
    exit 0
  fi

  # Find the backup file for the given date
  BACKUP_FILE=$(find "$BACKUP_FOLDER" -type f -name "backup_${RESTORE_DATE}_*.sql")

  # Check if a backup file was found
  if [ -z "$BACKUP_FILE" ]; then
    echo "No backup file found for date: $RESTORE_DATE"
    exit 0
  fi
  # Find all matching backup files and pick the latest one by modification time
  BACKUP_FILE=$(find "$BACKUP_FOLDER" -type f -name "backup_${RESTORE_DATE}_*.sql" -print0 |
    xargs -0 ls -t 2>/dev/null | head -n 1)

  # Confirm the restoration
  read -p "Are you sure you want to restore the database from this backup? (y/n): " CONFIRM

  if [[ $CONFIRM != "y" ]]; then
    echo "Restore operation cancelled."
    exit 1
  fi
  echo "Checking for active connections to $DB_NAME..."

  # Get count of active connections
  ACTIVE_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d postgres -h $DB_HOST -p $DB_PORT -t -c "
  SELECT count(*) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();
  " | xargs)

  if [ "$ACTIVE_COUNT" -gt 0 ]; then
    echo ""
    echo "⚠️  There are currently $ACTIVE_COUNT active connection(s) to $DB_NAME:"
    echo ""

    # Show details of active connections
    PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d postgres -h $DB_HOST -p $DB_PORT -c "
    SELECT pid, usename AS user, application_name, client_addr, state, query
    FROM pg_stat_activity
    WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();
    "

    echo ""
    read -p "Do you want to terminate all these connections? [y/N]: " CONFIRM

    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
      echo "Aborting. Database restore cancelled."
      exit 1
    fi

    echo "Terminating all active connections..."
    PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d postgres -h $DB_HOST -p $DB_PORT -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();
    "
  else
    echo "No active connections found. Proceeding..."
  fi

  echo ""
  echo "Dropping and recreating the database..."

  PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d postgres -h $DB_HOST -p $DB_PORT -c "DROP DATABASE IF EXISTS $DB_NAME;"
  PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d postgres -h $DB_HOST -p $DB_PORT -c "CREATE DATABASE $DB_NAME;"

  echo "Restoring the database from backup..."
  cat "$BACKUP_FILE" | PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -h $DB_HOST -d $DB_NAME -p $DB_PORT

  if [ $? -eq 0 ]; then
    echo "✅ Database restored successfully from backup: $BACKUP_FILE"
  else
    echo "❌ Database restore failed!"
    exit 1
  fi
fi
