#!/bin/bash

# Load variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found!"
  exit 1
fi
# Base docker-compose.yml file
MAIN_COMPOSE_FILE="docker-compose.yml"

# Create an array to store found docker-compose files
COMPOSE_FILES=("$MAIN_COMPOSE_FILE")

# Find all docker-compose.yml files in subdirectories
while IFS= read -r -d '' file; do
  COMPOSE_FILES+=(" -f $file")
done < <(find . -mindepth 2 -name "docker-compose.yml" -print0)

# Print the compose files to be used
echo "Detected docker-compose files: ${COMPOSE_FILES[*]}"

# Get the base command

if [[ "$1" == "up" ]]; then
  # Pull latest montrek-container image
  docker pull ghcr.io/montrek-software/montrek-container:latest
  COMMAND="up"
fi

if [[ "$1" == "down" ]]; then
  COMMAND="down"
fi

# Check for the -d flag
DETACHED=""
if [[ "$2" == "-d" ]]; then
  DETACHED="-d"
fi

BUILD=""
if [[ "$3" == "--build" ]]; then
  BUILD="--build"
fi
if [[ "$ENABLE_KEYCLOAK" == "1" ]]; then
  COMMAND=" --profile keycloak $COMMAND"
fi

# Inject dynamic UID and GID into .env
sed -i '/^USER_ID=/d' .env
sed -i '/^GROUP_ID=/d' .env
echo "USER_ID=$(id -u)" >>.env
echo "GROUP_ID=$(id -g)" >>.env
echo "docker compose -f "${COMPOSE_FILES[@]}" $COMMAND $DETACHED $BUILD --remove-orphans"
# Combine and run them
docker compose -f "${COMPOSE_FILES[@]}" $COMMAND $DETACHED $BUILD --remove-orphans
