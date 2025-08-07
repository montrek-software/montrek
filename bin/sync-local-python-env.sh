#!/bin/bash

echo "Syncing Python environment with uv..."
uv venv

# Combine all requirements.in files into one
temporary_requirements_file="all_requirements.in"
find . -name 'requirements.in' -exec cat {} + >"$temporary_requirements_file"

# Compile and sync using uv
uv pip compile "$temporary_requirements_file" --output-file requirements.txt
uv pip sync requirements.txt

rm "$temporary_requirements_file"
