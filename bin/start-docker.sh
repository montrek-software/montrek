#!/bin/bash

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

COMMAND="up"

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

# Combine and run them
docker compose -f "${COMPOSE_FILES[@]}" $COMMAND $DETACHED $BUILD --remove-orphans
