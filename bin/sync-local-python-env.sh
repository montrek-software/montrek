#!/bin/bash

# Install pip-tools
echo "Installing pip-tools..."
pip install pip-tools
temporary_requirements_file="all_requirements.txt"
find . -name 'requirements.txt' -exec cat {} + >"$temporary_requirements_file"
pip-sync "$temporary_requirements_file"
rm "$temporary_requirements_file"
