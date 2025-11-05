#!/bin/bash
export XDG_CACHE_HOME=/tmp/.cache
set -e

# Install instance-specific certs if provided
if [[ -f ./nginx/certs/fullchain.crt ]]; then
  echo "Installing instance-specific certificate..."
  cp ./nginx/certs/fullchain.crt /usr/local/share/ca-certificates/montrek_root_ca.crt
  update-ca-certificates
fi
./bin/local/sync-python-env.sh
. .venv/bin/activate
cd montrek
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runscript user.scripts.create_superuser
python -m gunicorn --chdir montrek montrek.wsgi:application --bind 0.0.0.0:${APP_PORT} --timeout 300
