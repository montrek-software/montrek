#!/bin/bash
set -euo pipefail

# shellcheck source=../lib/load-env.sh
. "$(dirname "${BASH_SOURCE[0]}")/../lib/load-env.sh"
montrek_load_env
montrek_require_env DB_ENGINE || exit 1

# Base compose file plus any nested ones. Each path is its own array element
# with its own -f, so a path containing a space still arrives as one argument.
COMPOSE_ARGS=(-f docker-compose.yml)
while IFS= read -r -d '' file; do
  COMPOSE_ARGS+=(-f "$file")
done < <(find . -mindepth 2 -name "docker-compose.yml" -not -path "./.venv/*" -print0)

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

set -x
docker compose "${COMPOSE_ARGS[@]}" "${PROFILE[@]}" "${COMMAND[@]}" --remove-orphans
