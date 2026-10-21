#!/bin/bash
# The one-off tasks of a deployment: database migrations, the static files and
# the superuser. Expects the venv to be active and montrek/ as the working
# directory. web-entrypoint.sh runs them on every start unless
# DO_MONTREK_STARTUP_TASKS is off; release-entrypoint.sh runs them on their own,
# once per deployment, before any web container starts.
set -e

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runscript user.scripts.create_superuser
