#!/bin/bash
set -e
echo "SERVICE is: $SERVICE"

# The container starts as root (compose sets `user: "0:0"`, overriding the
# image's USER) so privileged-entrypoint.sh can install the instance CA. From
# here on nothing needs root, so drop to an unprivileged uid before exec'ing
# the app.
#
# An app image (Dockerfile.app) has the code and the venv baked in, owned by
# root, and marks that with this file. The repo bind mount of a VM install hides
# it, so its absence means code, venv and their ownership come from the host.
# Checked inline rather than through a sourced helper: this script is also baked
# into the base image as /entrypoint.sh, which may run against an older checkout.
MONTREK_IMAGE_MARKER=/montrek/.montrek-image

# PUID/PGID normally come from the host user via compose. When they are absent
# -- someone ran `docker compose up` directly instead of `make docker-up` --
# fall back to whoever owns the mounted app directory, which is the uid that
# has to be able to write uploads/ and the venv anyway. An app image owns
# nothing under /montrek by the app user, so there it is the image's appuser.
if [[ -f "$MONTREK_IMAGE_MARKER" ]]; then
  : "${PUID:=$(id -u appuser)}"
  : "${PGID:=$(id -g appuser)}"
else
  : "${PUID:=$(stat -c %u /montrek)}"
  : "${PGID:=$(stat -c %g /montrek)}"
fi

# An app image normally starts as its unprivileged USER: there is nothing to
# drop and no root-only setup to do.
STARTED_AS_ROOT=false
[[ "$(id -u)" == "0" ]] && STARTED_AS_ROOT=true

# Refuse to run the app as root rather than silently doing it: this is exactly
# how the previous PIUD/PGUD typo went unnoticed. Set MONTREK_ALLOW_ROOT=1 to
# override deliberately.
if $STARTED_AS_ROOT && [[ "$PUID" == "0" || "$PGID" == "0" ]]; then
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
APP_HOME="${MONTREK_HOME:-/tmp/montrek-home}"
mkdir -p "$APP_HOME/.cache" "$APP_HOME/.config/matplotlib" "$APP_HOME/.local"

if $STARTED_AS_ROOT; then
  # Root-only setup, now that PUID/PGID are known: the CA install and repairing
  # the ownership of the paths the app writes.
  export PUID PGID
  /montrek/bin/entrypoints/privileged-entrypoint.sh
  chown -R "${PUID}:${PGID}" "$APP_HOME"
else
  # Without root the instance CA cannot go into the system store, so it is
  # appended to a private copy of the bundle, which requests (and with it the
  # OIDC client) and OpenSSL are pointed at.
  ca_cert="${MONTREK_CA_CERT:-/montrek/nginx/certs/fullchain.crt}"
  if [[ -f "$ca_cert" ]]; then
    echo "Adding $ca_cert to a private CA bundle..."
    cat /etc/ssl/certs/ca-certificates.crt "$ca_cert" >"$APP_HOME/ca-certificates.crt"
    export REQUESTS_CA_BUNDLE="$APP_HOME/ca-certificates.crt"
    export SSL_CERT_FILE="$APP_HOME/ca-certificates.crt"
  fi
fi

# gosu rewrites HOME from the target user's passwd entry, which a bare numeric
# uid does not have, so the environment is re-applied on the far side of it.
run_as_app_user() {
  local drop=()
  if $STARTED_AS_ROOT; then
    echo "Running $SERVICE as ${PUID}:${PGID} (HOME=$APP_HOME)..."
    drop=(gosu "${PUID}:${PGID}")
  else
    echo "Running $SERVICE as $(id -u):$(id -g) (HOME=$APP_HOME)..."
  fi
  exec "${drop[@]}" env \
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
release)
  run_as_app_user /montrek/bin/entrypoints/release-entrypoint.sh
  ;;
*)
  run_as_app_user "$@"
  ;;
esac
