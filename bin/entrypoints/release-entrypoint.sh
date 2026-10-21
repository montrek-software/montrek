#!/bin/bash
# The release step: the start-up tasks without gunicorn, for an install that
# runs several web containers or sets DO_MONTREK_STARTUP_TASKS=0. It has to
# finish before web and the workers start -- they share the venv it syncs, and
# none of them may run against an unmigrated database. With compose that is a
# one-shot service the others depend on with
# `condition: service_completed_successfully`.
set -e

[[ -f /montrek/.montrek-image ]] || ./bin/local/sync-python-env.sh
. .venv/bin/activate
cd montrek
/montrek/bin/entrypoints/startup-tasks.sh
