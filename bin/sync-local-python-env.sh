#!/bin/bash
# Load pyenv and pyenv-virtualenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
# Define the pyenv version name and Python version
pyenv_version_name="montrek-3.12.0"
python_version="3.12.0"

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

# Install pip-tools
echo "Installing pip-tools..."
pip install pip-tools
temporary_requirements_file="all_requirements.txt"
find . -name 'requirements.txt' -exec cat {} + >"$temporary_requirements_file"
pip-sync "$temporary_requirements_file"
rm "$temporary_requirements_file"
