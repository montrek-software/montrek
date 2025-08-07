#!/bin/bash
export XDG_CACHE_HOME=/tmp/.cache
set -e

make sync-local-python-env
. .venv/bin/activate
cd montrek
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runscript user.scripts.create_superuser
python -m gunicorn --chdir montrek montrek.wsgi:application --bind 0.0.0.0:${APP_PORT} --timeout 300
