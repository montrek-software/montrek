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

echo "Environment variables loaded successfully."
echo "DB Engine: $DB_ENGINE"
echo "DB Name: $DB_NAME"
echo "DB User: $DB_USER"
echo "DB Host: $DB_HOST"
echo "DB Port: $DB_PORT"

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
  find "$BACKUP_FOLDER" -type f -name "*.sql" -mtime +30 | while read FILE; do
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
  # Step 1: Clean the database by dropping all tables
  echo "Cleaning the database..."

  # Drop the existing database

  PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d postgres -h $DB_HOST -p $DB_PORT -c "DROP DATABASE IF EXISTS $DB_NAME;"

  # Recreate the database
  PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d postgres -h $DB_HOST -p $DB_PORT -c "CREATE DATABASE $DB_NAME;"

  # Step 2: Restore the database by running the backup file inside the Docker container
  cat "$BACKUP_FILE" | PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -h $DB_HOST -d $DB_NAME -p $DB_PORT

  # Check if the restore was successful
  if [ $? -eq 0 ]; then
    echo "Database restored successfully from backup: $BACKUP_FILE"
  else
    echo "Database restore failed!"
    exit 1
  fi
fi
