#!/usr/bin/env bash
# Create secrets/ and move every secret out of .env into its own file, so the
# stack can run with the secrets.yml compose overlay.
#
# Idempotent: a secret already in secrets/ is left alone, and a .env line that
# has already been migrated is not there to migrate again. Safe to re-run after
# adding a new value to .env.
#
# Run it as the user that runs `make docker-up`: the app containers drop to that
# uid, and Compose ignores the `uid`/`gid`/`mode` fields of a file secret, so the
# host file's ownership is what the container sees.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

# shellcheck source=../lib/secrets.sh
. bin/lib/secrets.sh

ENV_FILE=".env"
SECRETS_DIR="$MONTREK_SECRETS_DIR_HOST"
OVERLAY="secrets.yml"

# The declared list and the overlay have to agree: Compose fails on a `file:`
# source that does not exist, and run.sh decides whether to pass the overlay by
# checking the list.
check_overlay_matches_list() {
  local name missing=()
  for name in "${MONTREK_SECRET_NAMES[@]}"; do
    grep -qE "^  ${name}:\$" "$OVERLAY" || missing+=("$name")
  done
  if ((${#missing[@]})); then
    printf 'ERROR: %s declares secrets that %s does not: %s\n' \
      "bin/lib/secrets.sh" "$OVERLAY" "${missing[*]}" >&2
    exit 1
  fi
}

# The .env value for $1, using the same parsing as bin/lib/load-env.sh: first
# match wins, one pair of surrounding quotes is stripped. Never echoed.
env_file_value() {
  local key="$1" line value
  [[ -f "$ENV_FILE" ]] || return 0

  line="$(grep -m1 -E "^[[:space:]]*${key}[[:space:]]*=" "$ENV_FILE" || true)"
  [[ -n "$line" ]] || return 0

  value="${line#*=}"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  if [[ ${#value} -ge 2 ]] &&
    { [[ ${value:0:1} == '"' && ${value: -1} == '"' ]] ||
      [[ ${value:0:1} == "'" && ${value: -1} == "'" ]]; }; then
    value="${value:1:${#value}-2}"
  fi
  printf '%s' "$value"
}

# Replace the line with a marker rather than deleting it, so the file still
# documents where the value went. The value itself is not kept anywhere: a
# commented-out password is still a password on disk, and .env.bak files are
# exactly how this went wrong before.
strip_from_env_file() {
  local key="$1"
  sed -i -E "s|^[[:space:]]*${key}[[:space:]]*=.*|# ${key} moved to ${SECRETS_DIR}/${key,,} by 'make secrets-init'|" "$ENV_FILE"
}

# The current value of $1, wherever it lives: .env, or the secret file it has
# already been migrated into. The fallback secrets are resolved through this, so
# re-running after ADMIN_PASSWORD has moved still finds it.
resolve_value() {
  local variable="$1" value path
  value="$(env_file_value "$variable")"
  if [[ -z "$value" ]]; then
    path="${SECRETS_DIR}/${variable,,}"
    [[ -s "$path" ]] && value="$(cat -- "$path")"
  fi
  printf '%s' "$value"
}

write_secret() {
  local name="$1" value="$2" mode
  mode="$(montrek_secret_mode "$name")"

  # Create it empty first so the value never exists at the default umask.
  : >"${SECRETS_DIR}/${name}"
  chmod "$mode" "${SECRETS_DIR}/${name}"
  # No trailing newline, so `cat` and a plain read agree with what Django sees.
  printf '%s' "$value" >"${SECRETS_DIR}/${name}"
}

check_overlay_matches_list

mkdir -p "$SECRETS_DIR"
# The host-side gate. Compose hands the container the file as it is, so the
# world-readable ones rely on this directory to stay private on the host.
chmod 700 "$SECRETS_DIR"

created=() migrated=() kept=()

for name in "${MONTREK_SECRET_NAMES[@]}"; do
  variable="$(montrek_secret_variable "$name")"
  path="${SECRETS_DIR}/${name}"

  if [[ -s "$path" ]]; then
    chmod "$(montrek_secret_mode "$name")" "$path"
    kept+=("$name")
    # A value left in .env would win over the file, because the environment
    # outranks every file source. Take it out.
    if [[ -f "$ENV_FILE" ]] && grep -qE "^[[:space:]]*${variable}[[:space:]]*=" "$ENV_FILE"; then
      strip_from_env_file "$variable"
      printf '  %-24s removed a stale %s from .env\n' "$name" "$variable"
    fi
    continue
  fi

  value="$(env_file_value "$variable")"

  # Carry over the fallback the compose file applied, so a secret that was
  # never set explicitly keeps the protection it had.
  fallback_variable="$(montrek_secret_fallback_variable "$name")"
  if [[ -z "$value" && -n "$fallback_variable" ]]; then
    value="$(resolve_value "$fallback_variable")"
    [[ -n "$value" ]] && printf '  %-24s seeded from %s (its previous fallback)\n' \
      "$name" "$fallback_variable"
  fi

  if [[ -n "$value" ]]; then
    write_secret "$name" "$value"
    # Only a value of its own is removed from .env: ADMIN_PASSWORD is a secret
    # in its own right and is migrated by its own pass through this loop.
    [[ -n "$(env_file_value "$variable")" ]] && strip_from_env_file "$variable"
    migrated+=("$name")
  else
    # Declared but unused by this install. Compose needs the file to exist;
    # an empty one counts as unset everywhere that reads it.
    write_secret "$name" ""
    created+=("$name")
  fi
done

report() {
  local label="$1"
  shift
  (($#)) || return 0
  printf '%s: %s\n' "$label" "$*"
}

echo
report "Migrated from .env" "${migrated[@]+"${migrated[@]}"}"
report "Already present   " "${kept[@]+"${kept[@]}"}"
report "Created empty     " "${created[@]+"${created[@]}"}"
echo
echo "secrets/ is ready. 'make docker-up' now passes -f ${OVERLAY} automatically."
echo

if [[ ! -s "${SECRETS_DIR}/secret_key" || ! -s "${SECRETS_DIR}/db_password" ]]; then
  echo "WARNING: secret_key and db_password are empty. The app will fall back to" >&2
  echo "  .env for them, or fail to start if they are not there either." >&2
fi

echo "Next:"
echo "  - Fill in any secret you want that this install does not have yet, e.g."
echo "      printf '%s' 'a strong password' > ${SECRETS_DIR}/flower_password"
echo "  - Restart the stack:  make docker-restart"
echo "  - Check that nothing leaks:"
echo "      docker compose -f docker-compose.yml -f secrets.yml config | grep -i -e password -e secret_key"
