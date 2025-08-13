#!/usr/bin/env bash
set -euo pipefail

# Detect if we have a TTY (useful for CI where you may need -T).
TTY_FLAG=""
if [ ! -t 1 ]; then
  TTY_FLAG="-T"
fi

# If your venv/python or manage.py lives elsewhere, tweak these:
PYTHON_IN_VENV=".venv/bin/python"
MANAGE_PY="montrek/manage.py"

# Exec inside the running `web` service, forwarding all args to manage.py.
# Example: ./django-manage.sh migrate
#          ./django-manage.sh runscript my_script -- --opt=val
exec docker compose exec ${TTY_FLAG} web \
  "${PYTHON_IN_VENV}" "${MANAGE_PY}" "$@"
