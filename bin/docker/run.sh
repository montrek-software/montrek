#!/bin/bash
set -euo pipefail

# shellcheck source=../lib/load-env.sh
. "$(dirname "${BASH_SOURCE[0]}")/../lib/load-env.sh"
# shellcheck source=../lib/secrets.sh
. "$(dirname "${BASH_SOURCE[0]}")/../lib/secrets.sh"
montrek_load_env
montrek_require_env DB_ENGINE || exit 1

# Base compose file plus any nested ones. Each path is its own array element
# with its own -f, so a path containing a space still arrives as one argument.
COMPOSE_ARGS=(-f docker-compose.yml)
while IFS= read -r -d '' file; do
  COMPOSE_ARGS+=(-f "$file")
done < <(find . -mindepth 2 -name "docker-compose.yml" -not -path "./.venv/*" -print0)

# The file-based secrets overlay, once `make secrets-init` has created every
# file it declares. Compose fails outright on a missing `file:` source, so this
# is all-or-nothing rather than per secret, and an install that has not migrated
# keeps reading everything from .env.
if montrek_secrets_initialized; then
  COMPOSE_ARGS+=(-f secrets.yml)
else
  echo "Secrets are in .env; run 'make secrets-init' to move them into ${MONTREK_SECRETS_DIR_HOST}/." >&2
fi

# The container entrypoint drops privileges to this uid/gid, which has to be
# the owner of the bind-mounted repo. Exported rather than written into .env:
# compose interpolation reads the environment, and the previous `sed -i` edited
# the same secrets file that bin/secrets/ is trying to keep intact.
export USER_ID="$(id -u)"
export GROUP_ID="$(id -g)"

COMMAND=()
case "${1:-}" in
up) COMMAND=(up) ;;
down) COMMAND=(down) ;;
*)
  echo "Usage: $0 {up|down} [-d] [--build]" >&2
  exit 1
  ;;
esac

[[ "${2:-}" == "-d" ]] && COMMAND+=(-d)
[[ "${3:-}" == "--build" ]] && COMMAND+=(--build)

PROFILE=()
if [[ "${ENABLE_KEYCLOAK:-0}" == "1" ]]; then
  PROFILE=(--profile keycloak)
fi

# Strip any USER_ID/GROUP_ID left in .env by an older version of this script,
# so the exported values are what actually takes effect.
if [[ -f .env ]] && grep -qE '^(USER_ID|GROUP_ID)=' .env; then
  echo "Removing stale USER_ID/GROUP_ID entries from .env"
  sed -i -E '/^(USER_ID|GROUP_ID)=/d' .env
fi

# montrek_load_env resolves secrets into the environment for the scripts that
# need them; compose must not see them. Every value in its environment is a
# candidate for `${...}` interpolation, and interpolating a secret is exactly
# what this whole overlay exists to stop -- it would put the value straight back
# into the container config, and set POSTGRES_PASSWORD alongside
# POSTGRES_PASSWORD_FILE, which postgres refuses to start with.
for secret_name in "${MONTREK_SECRET_NAMES[@]}"; do
  unset "$(montrek_secret_variable "$secret_name")"
done

set -x
docker compose "${COMPOSE_ARGS[@]}" "${PROFILE[@]}" "${COMMAND[@]}" --remove-orphans
