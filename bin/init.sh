#!/bin/bash

#Setup python environment
PYTHON_VERSION=3.12.0
PROJECT_NAME=$(basename "$PWD")
ENV_NAME="$PROJECT_NAME-$PYTHON_VERSION"
echo "$ENV_NAME" >.python-version

# Check if virtualenv already exists
if pyenv virtualenvs --bare | grep -q "^$ENV_NAME$"; then
  echo "Virtualenv '$ENV_NAME' already exists. Skipping creation."
else
  echo "Creating virtualenv '$ENV_NAME'..."
  pyenv virtualenv "$PYTHON_VERSION" "$ENV_NAME"
fi
make sync-local-python-env
