#!/usr/bin/env bash
# Configuration loading, shared by the bin/ scripts.
#
# Values already present in the environment always win; only the gaps are
# filled in from the file. That means a caller which is handed its
# configuration directly -- a container started with `env_file:`, or CI --
# needs no .env file at all, and a missing file is not an error for it.
#
# Parsing deliberately mirrors python-decouple's RepositoryEnv (skip blank and
# comment lines, split on the first `=`, strip whitespace, strip one matching
# pair of surrounding quotes) so the shell scripts and Django agree on what a
# given line means.
#
# Source it, don't execute it:  . bin/lib/load-env.sh

montrek_load_env() {
  local env_file="${1:-.env}"

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
