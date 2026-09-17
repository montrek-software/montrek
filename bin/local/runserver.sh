#!/bin/bash
# Configuration comes from the environment first and only then from .env, so
# this works unchanged on the host and inside a container where .env is
# deliberately shadowed.
# shellcheck source=../lib/load-env.sh
. "$(dirname "${BASH_SOURCE[0]}")/../lib/load-env.sh"
montrek_load_env

montrek_require_env APP_PORT || exit 1

echo "Environment variables loaded successfully."
echo "App Port: $APP_PORT"

cd montrek/
python manage.py migrate
python manage.py runserver $APP_PORT
