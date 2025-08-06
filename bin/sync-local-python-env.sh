#!/bin/bash

# Install pip-tools
echo "Installing pip-tools..."
pip install pip-tools
temporary_requirements_file="all_requirements.in"
find . -name 'requirements.in' -exec cat {} + >"$temporary_requirements_file"
pip-compile "$temporary_requirements_file"
pip-sync all_requirements.txt
rm "$temporary_requirements_file"
