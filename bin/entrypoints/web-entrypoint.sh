#!/bin/bash
# HOME and the XDG cache/config dirs are set by montrek-entrypoint.sh.
set -e

# The instance CA is installed by privileged-entrypoint.sh, which still has
# root. Doing it again here fails now that this script genuinely runs
# unprivileged -- /usr/local/share/ca-certificates is not writable by PUID.

./bin/local/sync-python-env.sh
. .venv/bin/activate
cd montrek
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runscript user.scripts.create_superuser
# Several workers with threads, so one slow request (e.g. the risk values
# report and its summary refresh) no longer blocks every other user. Gunicorn
# defaults to a single sync worker. Tunable via .env without a rebuild.
python -m gunicorn --chdir montrek montrek.wsgi:application \
  --bind 0.0.0.0:${APP_PORT} \
  --workers "${GUNICORN_WORKERS:-4}" \
  --worker-class gthread \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --max-requests 500 \
  --max-requests-jitter 50
