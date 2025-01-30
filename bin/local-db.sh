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

if [[ "$1" == "create" ]]; then
	if [[ "$DB_ENGINE" = "postgres" ]]; then
		POSTGRES_PATH=/usr/local/var/postgres
		if [ ! -d "$POSTGRES_PATH" ]; then
			# Set access rights
			sudo mkdir -p $POSTGRES_PATH
			sudo chown -R $(whoami) $POSTGRES_PATH
			chmod 775 $POSTGRES_PATH
			echo "Initializing PostgreSQL database..."
			initdb -D $POSTGRES_PATH --username=postgres --pwfile=<(echo "$DB_PASSWORD")
		fi

		# Start PostgreSQL
		echo "Starting PostgreSQL server..."
		pg_ctl -D $POSTGRES_PATH -o "-p $DB_PORT" start

		# Wait for PostgreSQL to be ready
		echo "Waiting for PostgreSQL to be ready..."
		sleep 5

		# Check if the 'postgres' role exists
		echo "Checking if the 'postgres' superuser exists..."
		SUPERUSER_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -tAc "SELECT 1 FROM pg_roles WHERE rolname='postgres';" -U postgres -d $DB_NAME)
		if [[ "$SUPERUSER_EXISTS" != "1" ]]; then
			echo "Error: 'postgres' role does not exist. Please ensure initdb has created it correctly."
			exit 1
		fi
		# Create the user if it doesn't exist
		echo "Checking if the user '$DB_USER' exists..."
		USER_EXISTS=$(psql -U postgres -h "$DB_HOST" -p "$DB_PORT" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER';")
		if [[ "$USER_EXISTS" != "1" ]]; then
			echo "Creating user '$DB_USER'..."
			createuser -U postgres -p "$DB_PORT" "$DB_USER"
		fi

		# Set the user's password
		echo "Setting password for user '$DB_USER'..."
		psql -U postgres -p "$DB_PORT" -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

		echo "Start creating the database..."
		# Connect to the PostgreSQL server and execute the SQL commands
		psql -U postgres -p $DB_PORT -d $DB_NAME -c "CREATE DATABASE $DB_NAME;" 2>/dev/null

		if [ $? -eq 0 ]; then
			echo "Database '$DB_NAME' created successfully."
		else
			echo "Failed to create database '$DB_NAME'. It might already exist or there was an error."
		fi

		# Create a database user (if needed)
		echo "Checking if the user '$DB_USER' exists..."
		USER_EXISTS=$(psql -h $DB_HOST -U postgres -p $DB_PORT -d $DB_NAME -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER';")

		if [[ "$USER_EXISTS" == "1" ]]; then
			echo "User '$DB_USER' already exists."
		else
			echo "Creating user '$DB_USER'..."
			PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -p $DB_PORT -d $DB_NAME -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
			echo "User '$DB_USER' created successfully."
		fi

		# Grant privileges to the user
		echo "Granting privileges to user '$DB_USER' on database '$DB_NAME'..."
		psql -h $DB_HOST -U postgres -p $DB_PORT -d $DB_NAME -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
		psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -d $DB_NAME -c "GRANT USAGE ON SCHEMA public TO $DB_USER;"
		psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -d $DB_NAME -c "GRANT CREATE ON SCHEMA public TO $DB_USER;"
		psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -d $DB_NAME -c "ALTER USER $DB_USER CREATEDB;"

		echo "Database setup completed successfully."
	else
		echo "Unsupported database engine: $DB_ENGINE"
		exit
	fi
elif [[ "$1" == "backup" ]]; then
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

fi
