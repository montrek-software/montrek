#!/bin/bash

# Load variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found!"
  exit 1
fi
# Check if required variables are set
missing_vars=()

if [[ -z "$SONARCUBE_URL" ]]; then
  missing_vars+=("SONARCUBE_URL")
fi

if [[ -z "$SONARCUBE_TOKEN" ]]; then
  missing_vars+=("SONARCUBE_TOKEN")
fi

if [[ ${#missing_vars[@]} -ne 0 ]]; then
  echo "One or more required environment variables are missing in .env:"
  for var in "${missing_vars[@]}"; do
    echo "$var"
  done
  exit 1
fi
