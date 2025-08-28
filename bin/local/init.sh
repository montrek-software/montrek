#!/bin/bash

#Setup python environment
PYTHON_VERSION=3.12.0
PROJECT_NAME=$(basename "$PWD")
ENV_NAME="$PROJECT_NAME-$PYTHON_VERSION"
echo "$ENV_NAME" >.python-version

# Load pyenv and pyenv-virtualenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
# Define the pyenv version name and Python version
pyenv_version_name=$ENV_NAME
python_version=PYTHON_VERSION

# Check if the pyenv version exists
if ! pyenv versions | grep -q "$pyenv_version_name"; then
  echo "Pyenv version $pyenv_version_name not found. Creating it with Python $python_version..."
  pyenv install -s "$python_version"
  pyenv virtualenv "$python_version" "$pyenv_version_name"
else
  echo "Pyenv version $pyenv_version_name already exists."
fi

# Check if the pyenv version is activated
current_pyenv_version=$(pyenv version-name)
if [ "$current_pyenv_version" != "$pyenv_version_name" ]; then
  echo "Activating pyenv version $pyenv_version_name..."
  echo "pyenv activate $pyenv_version_name"
  pyenv activate "$pyenv_version_name"
else
  echo "Pyenv version $pyenv_version_name is already active."
fi
# Check if virtualenv already exists
if pyenv virtualenvs --bare | grep -q "^$ENV_NAME$"; then
  echo "Virtualenv '$ENV_NAME' already exists. Skipping creation."
else
  echo "Creating virtualenv '$ENV_NAME'..."
  pyenv virtualenv "$PYTHON_VERSION" "$ENV_NAME"
fi
pip install uv
make sync-local-python-env
python -m pre_commit install
