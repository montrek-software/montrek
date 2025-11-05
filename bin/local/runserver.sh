#!/bin/bash
# Load variables from .env file
if [ -f .env ]; then
	export $(grep -v '^#' .env | xargs)
else
	echo ".env file not found!"
	exit 1
fi

# Check if required variables are set
if [[ -z "$APP_PORT" ]]; then
	echo "One or more required environment variables are missing in .env:"
	echo "APP_PORT"
	exit 1
fi

echo "Environment variables loaded successfully."
echo "App Port: $APP_PORT"

cd montrek/
python manage.py migrate
python manage.py runserver $APP_PORT
