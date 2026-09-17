#!/usr/bin/env bash
# Configuration loading, shared by the bin/ scripts.
#
# Values already present in the environment always win; only the gaps are
# filled in, first from mounted secrets and then from the file. That means a
# caller which is handed its configuration directly -- a container started with
# `env_file:`, or CI -- needs no .env file at all, and a missing file is not an
# error for it.
#
# The order matches montrek/configuration.py, so a script run inside a container
# and the Django process next to it resolve every value the same way:
#
#   environment  >  NAME_FILE  >  /run/secrets/name  >  .env  >  built-in default
#
# Parsing deliberately mirrors python-decouple's RepositoryEnv (skip blank and
# comment lines, split on the first `=`, strip whitespace, strip one matching
# pair of surrounding quotes) so the shell scripts and Django agree on what a
# given line means.
#
# Source it, don't execute it:  . bin/lib/load-env.sh

# Fill in variables backed by a file rather than by the environment: a
# `NAME_FILE=/path` pointer, and every file in the secrets directory, whose name
# is the variable it stands for, lowercased (`db_password` -> `DB_PASSWORD`).
#
# Trailing newlines are stripped and an empty file counts as unset, matching
# FileAwareConfig in montrek/configuration.py -- init-secrets.sh has to create a
# file for every secret the compose overlay declares, so the unused ones are
# empty rather than absent.
montrek_load_secrets() {
  # /run/secrets is where compose mounts them; secrets/ next to .env is where
  # `make secrets-init` writes them and the only one a non-Docker run on the
  # host has. Inside a container that second path is /montrek/secrets, which the
  # compose files shadow with an empty tmpfs, so it never answers there.
  # MONTREK_SECRETS_DIR replaces the search rather than adding to it.
  local dirs=("/run/secrets" "$(dirname -- "${1:-.env}")/secrets")
  [[ -n "${MONTREK_SECRETS_DIR:-}" ]] && dirs=("$MONTREK_SECRETS_DIR")
  local dir pointer target file name value

  # NAME_FILE pointers, which is how postgres, mariadb and keycloak are wired
  # and how a secret whose file name differs from its variable is resolved.
  while IFS= read -r pointer; do
    target="${pointer%_FILE}"
    [[ -n "$target" && ! -v "$target" ]] || continue
    file="${!pointer}"
    [[ -n "$file" ]] || continue
    montrek_read_secret_file "$file" "$target"
  done < <(awk 'BEGIN { for (v in ENVIRON) if (v ~ /^[A-Za-z_][A-Za-z0-9_]*_FILE$/) print v }')

  for dir in "${dirs[@]}"; do
    [[ -d "$dir" ]] || continue
    for file in "$dir"/*; do
      [[ -f "$file" ]] || continue
      name="${file##*/}"
      [[ "$name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
      name="${name^^}"
      # Already set, by the environment or by an earlier directory in the list.
      [[ -v "$name" ]] && continue
      montrek_read_secret_file "$file" "$name"
    done
  done

  # Never fail the caller: a secret that cannot be read is reported by whatever
  # needs it (montrek_require_env, or Django), with the name of the variable.
  return 0
}

# Export $2 from the contents of $1, unless the file is unreadable or empty.
montrek_read_secret_file() {
  local file="$1" name="$2" value

  [[ -r "$file" ]] || return 0
  # $( ) already drops trailing newlines; CR is dropped for a file written on
  # Windows, so the same password does not depend on the editor that wrote it.
  value="$(cat -- "$file" 2>/dev/null)" || return 0
  value="${value%$'\r'}"
  [[ -n "$value" ]] || return 0

  export "$name=$value"
}

montrek_load_env() {
  local env_file="${1:-.env}"

  # Before the file: a mounted secret outranks .env, and both lose to a value
  # that is already exported. The path is passed on so the secrets/ directory
  # next to that .env is searched too.
  montrek_load_secrets "$env_file"

  # Not a regular readable file (absent, or shadowed by /dev/null inside a
  # container): whatever is already exported is all there is.
  [[ -f "$env_file" && -r "$env_file" ]] || return 0

  local line key value
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    [[ -z "$line" || "$line" == \#* || "$line" != *=* ]] && continue

    key="${line%%=*}"
    key="${key%"${key##*[![:space:]]}"}"
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue

    # Set already -- even to the empty string -- means the environment wins.
    [[ -v "$key" ]] && continue

    value="${line#*=}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    if [[ ${#value} -ge 2 ]] &&
      { [[ ${value:0:1} == '"' && ${value: -1} == '"' ]] ||
        [[ ${value:0:1} == "'" && ${value: -1} == "'" ]]; }; then
      value="${value:1:${#value}-2}"
    fi

    export "$key=$value"
  done <"$env_file"
}

# Fail with a single actionable message rather than one `if [[ -z ... ]]` per
# variable, and without ever echoing a value.
montrek_require_env() {
  local missing=() name
  for name in "$@"; do
    [[ -n "${!name:-}" ]] || missing+=("$name")
  done
  if ((${#missing[@]})); then
    printf 'Missing required configuration: %s\n' "${missing[*]}" >&2
    printf 'Set them in the environment or in .env\n' >&2
    return 1
  fi
}
