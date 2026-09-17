#!/usr/bin/env bash
# The secrets the compose overlay declares, shared by bin/secrets/init-secrets.sh
# and bin/docker/run.sh.
#
# Naming rule: a secret file is named after the environment variable it
# replaces, lowercased. `secrets/db_password` provides `DB_PASSWORD`. Compose
# mounts it at `/run/secrets/db_password`, and both montrek/configuration.py and
# montrek_load_secrets() in bin/lib/load-env.sh map the name back. Nothing has to
# be wired per variable, so nothing can drift.
#
# Keep this list and the `secrets:` block in secrets.yml in step -- Compose
# refuses to start when a declared secret file is missing, which is why
# init-secrets.sh creates all of them and leaves the unused ones empty.
#
# Source it, don't execute it:  . bin/lib/secrets.sh

MONTREK_SECRETS_DIR_HOST="${MONTREK_SECRETS_DIR_HOST:-secrets}"

MONTREK_SECRET_NAMES=(
  secret_key
  db_password
  admin_password
  email_host_password
  flower_password
  keycloak_admin_password
  keycloak_db_password
  keycloak_client_secret
)

# Secrets read by a container that does not run as the host user. Compose
# ignores the `uid`/`gid`/`mode` fields of a file secret -- it warns about it
# and bind-mounts the host file as it is -- so the only way postgres (uid 999),
# flower (uid 1000) and keycloak (uid 1000) can read their own password is for
# the file to be world-readable.
#
# That costs less than it looks like: the app containers run as the host user,
# who *owns* every one of these files, so 0600 would not stop a compromised
# montrek container from reading them either. The host-side gate is the 0700
# secrets/ directory, and the ceiling on all of it is docker group membership.
MONTREK_WORLD_READABLE_SECRETS=(
  db_password
  flower_password
  keycloak_admin_password
  keycloak_db_password
  keycloak_client_secret
)

# The variable a secret falls back to when its own is not set in .env.
# docker-compose.yml has always defaulted the Flower and Keycloak admin
# passwords to ADMIN_PASSWORD, so migrating has to carry that over: writing an
# empty secrets/flower_password instead would silently drop Flower's basic auth
# to `admin` with an empty password, which it accepts.
montrek_secret_fallback_variable() {
  case "$1" in
  flower_password | keycloak_admin_password) echo ADMIN_PASSWORD ;;
  *) echo "" ;;
  esac
}

montrek_secret_mode() {
  local name="$1" world_readable
  for world_readable in "${MONTREK_WORLD_READABLE_SECRETS[@]}"; do
    [[ "$name" == "$world_readable" ]] && {
      echo 0644
      return 0
    }
  done
  echo 0600
}

# The environment variable a secret file stands in for.
montrek_secret_variable() {
  local name="$1"
  echo "${name^^}"
}

# True when every declared secret file exists, i.e. when `docker compose` can be
# handed secrets.yml without failing on a missing `file:` source.
montrek_secrets_initialized() {
  local name
  for name in "${MONTREK_SECRET_NAMES[@]}"; do
    [[ -f "${MONTREK_SECRETS_DIR_HOST}/${name}" ]] || return 1
  done
  return 0
}
