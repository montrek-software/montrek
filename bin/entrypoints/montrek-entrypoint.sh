#!/bin/bash
set -e
echo "SERVICE is: $SERVICE"

# The container starts as root (compose sets `user: "0:0"`, overriding the
# image's USER) so privileged-entrypoint.sh can install the instance CA. From
# here on nothing needs root, so drop to an unprivileged uid before exec'ing
# the app.
#
# PUID/PGID normally come from the host user via compose. When they are absent
# -- someone ran `docker compose up` directly instead of `make docker-up` --
# fall back to whoever owns the mounted app directory, which is the uid that
# has to be able to write uploads/ and the venv anyway.
: "${PUID:=$(stat -c %u /montrek)}"
: "${PGID:=$(stat -c %g /montrek)}"

# Refuse to run the app as root rather than silently doing it: this is exactly
# how the previous PIUD/PGUD typo went unnoticed. Set MONTREK_ALLOW_ROOT=1 to
# override deliberately.
if [[ "$PUID" == "0" || "$PGID" == "0" ]]; then
  if [[ "${MONTREK_ALLOW_ROOT:-0}" != "1" ]]; then
    echo "ERROR: refusing to run $SERVICE as root (PUID=$PUID PGID=$PGID)." >&2
    echo "  /montrek is owned by uid $(stat -c %u /montrek), gid $(stat -c %g /montrek)." >&2
    echo "  Start the stack with 'make docker-up' so USER_ID/GROUP_ID are set," >&2
    echo "  or set MONTREK_ALLOW_ROOT=1 to override." >&2
    exit 1
  fi
  echo "WARN: running $SERVICE as root because MONTREK_ALLOW_ROOT=1" >&2
fi

# PUID has no /etc/passwd entry and therefore no home directory, so anything
# that caches under $HOME (matplotlib, uv, fontconfig, chromium, texlive's font
# cache) would try to write to / and fail. This went unnoticed while every
# service ran as root with HOME=/root.
# Root-only setup, now that PUID/PGID are known: the CA install and repairing
# the ownership of the paths the app writes.
export PUID PGID
/montrek/bin/entrypoints/privileged-entrypoint.sh

APP_HOME="${MONTREK_HOME:-/tmp/montrek-home}"
mkdir -p "$APP_HOME/.cache" "$APP_HOME/.config/matplotlib" "$APP_HOME/.local"
chown -R "${PUID}:${PGID}" "$APP_HOME"

# gosu rewrites HOME from the target user's passwd entry, which a bare numeric
# uid does not have, so the environment is re-applied on the far side of it.
run_as_app_user() {
  echo "Running $SERVICE as ${PUID}:${PGID} (HOME=$APP_HOME)..."
  exec gosu "${PUID}:${PGID}" env \
    HOME="$APP_HOME" \
    XDG_CACHE_HOME="$APP_HOME/.cache" \
    XDG_CONFIG_HOME="$APP_HOME/.config" \
    MPLCONFIGDIR="$APP_HOME/.config/matplotlib" \
    "$@"
}

case "$SERVICE" in
web)
  run_as_app_user /montrek/bin/entrypoints/web-entrypoint.sh
  ;;
sequential_worker | parallel_worker | fast_worker)
  run_as_app_user /montrek/bin/entrypoints/worker-entrypoint.sh
  ;;
celery_beat)
  run_as_app_user /montrek/bin/entrypoints/celery_beat-entrypoint.sh
  ;;
*)
  run_as_app_user "$@"
  ;;
esac
