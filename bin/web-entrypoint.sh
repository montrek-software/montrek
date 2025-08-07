#!/bin/bash
cp ./nginx/certs/fullchain.crt /usr/local/share/ca-certificates/montrek_root_ca.crt &&
  update-ca-certificates &&
  make sync-local-python-env &&
  . .venv/bin/activate &&
  cd montrek &&
  python manage.py migrate &&
  python manage.py collectstatic --noinput &&
  python manage.py runscript user.scripts.create_superuser &&
  python -m gunicorn --chdir montrek montrek.wsgi:application --bind 0.0.0.0:${APP_PORT} --timeout 300
