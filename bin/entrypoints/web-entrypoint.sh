#!/bin/bash
# HOME and the XDG cache/config dirs are set by montrek-entrypoint.sh.
set -e

# The instance CA is installed by privileged-entrypoint.sh, which still has
# root. Doing it again here fails now that this script genuinely runs
# unprivileged -- /usr/local/share/ca-certificates is not writable by PUID.

./bin/local/sync-python-env.sh
. .venv/bin/activate
cd montrek
# On by default, so a single-container install migrates on every start. Off
# where release-entrypoint.sh runs them once per deployment instead. Accepts the
# boolean spellings python-decouple does.
case "${DO_MONTREK_STARTUP_TASKS:-1}" in
[1yYtT] | [yY][eE][sS] | [tT][rR][uU][eE] | [oO][nN])
  /montrek/bin/entrypoints/startup-tasks.sh
  ;;
[0nNfF] | [nN][oO] | [fF][aA][lL][sS][eE] | [oO][fF][fF])
  echo "DO_MONTREK_STARTUP_TASKS is off: skipping migrate, collectstatic and the superuser."
  ;;
*)
  echo "ERROR: DO_MONTREK_STARTUP_TASKS=${DO_MONTREK_STARTUP_TASKS} is not a boolean." >&2
  exit 1
  ;;
esac
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
