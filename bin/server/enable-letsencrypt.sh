#!/bin/bash
# Wire an existing Let's Encrypt certificate into the nginx container and make
# renewals take effect automatically.
#
# This does NOT obtain certificates -- run certbot yourself first. It checks that
# a usable lineage exists, installs the certbot deploy hook, and prints the .env
# lines to add. It never edits .env, and it is safe to re-run.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOK_DIR=/etc/letsencrypt/renewal-hooks/deploy
HOOK_NAME=montrek-reload-nginx.sh

red()   { printf '\033[0;31m%s\033[0m\n' "$*"; }
green() { printf '\033[0;32m%s\033[0m\n' "$*"; }
warn()  { printf '\033[0;33m%s\033[0m\n' "$*"; }

fail() { red "ERROR: $*"; exit 1; }

# --- read the hostnames this deployment serves ---------------------------------
[[ -f "$REPO_DIR/.env" ]] || fail "no .env in $REPO_DIR"
# shellcheck disable=SC1091
PROJECT_NAME=$(grep -E '^PROJECT_NAME=' "$REPO_DIR/.env" | cut -d= -f2- | tr -d '"'"'"' ')
DEPLOY_HOST=$(grep -E '^DEPLOY_HOST=' "$REPO_DIR/.env" | cut -d= -f2- | tr -d '"'"'"' ')
ENABLE_KEYCLOAK=$(grep -E '^ENABLE_KEYCLOAK=' "$REPO_DIR/.env" | cut -d= -f2- | tr -d '"'"'"' ' || true)

[[ -n "$PROJECT_NAME" && -n "$DEPLOY_HOST" ]] || fail "PROJECT_NAME/DEPLOY_HOST not set in .env"

REQUIRED=("${PROJECT_NAME}.${DEPLOY_HOST}" "flower-${PROJECT_NAME}.${DEPLOY_HOST}")
[[ "$ENABLE_KEYCLOAK" == "1" ]] && REQUIRED+=("auth-${PROJECT_NAME}.${DEPLOY_HOST}")

echo "Hostnames this deployment serves:"
printf '  %s\n' "${REQUIRED[@]}"
echo

# --- find a lineage covering all of them ---------------------------------------
command -v certbot >/dev/null || fail "certbot not installed"

# `certbot certificates` needs root to read /etc/letsencrypt. Without it the
# listing comes back empty, which must not be reported as "no cert found".
if ! CERT_LIST=$(certbot certificates 2>&1); then
  red "$CERT_LIST"
  fail "could not read certificates${EUID:+ (try: sudo make server-enable-letsencrypt)}"
fi

mapfile -t LINEAGES < <(awk -F': *' '/Certificate Name:/{print $2}' <<<"$CERT_LIST")
if [[ ${#LINEAGES[@]} -eq 0 ]]; then
  [[ $EUID -ne 0 ]] && fail "no certificates visible -- run with sudo"
  fail "certbot has no certificates yet. Obtain one with:
  sudo certbot certonly --standalone $(printf -- '-d %s ' "${REQUIRED[@]}")"
fi

# Exact match per domain. Substring/word matching is wrong here: with `grep -w`,
# "web.example.com" matches inside "flower-web.example.com" because '-' counts
# as a word boundary, which would happily select a cert missing the bare host.
covers() {
  local needle=$1 d
  shift
  for d in "$@"; do [[ "$d" == "$needle" ]] && return 0; done
  return 1
}

BEST=""
for name in "${LINEAGES[@]}"; do
  [[ -n "$name" ]] || continue
  read -r -a have <<<"$(certbot certificates --cert-name "$name" 2>/dev/null \
                        | awk -F': *' '/^ *Domains:/{print $2}')"
  missing=()
  for d in "${REQUIRED[@]}"; do
    covers "$d" "${have[@]}" || missing+=("$d")
  done
  if [[ ${#missing[@]} -eq 0 ]]; then
    green "  $name covers all required hostnames"
    BEST="$name"
  else
    warn  "  $name is missing: ${missing[*]}"
  fi
done

[[ -n "$BEST" ]] || fail "no existing certificate covers all required hostnames.
Check the list above -- if one is close, extend it rather than creating a new
lineage (duplicate lineages are how -0001/-0002 happen, and re-issuing burns
Let's Encrypt rate limits). To create one:
  sudo certbot certonly --standalone --cert-name montrek-${PROJECT_NAME} \\
    $(printf -- '-d %s ' "${REQUIRED[@]}")"

# --- install the deploy hook ---------------------------------------------------
if [[ $EUID -ne 0 ]]; then
  warn "Not running as root; skipping hook installation."
  warn "Re-run with sudo to install $HOOK_DIR/$HOOK_NAME"
else
  mkdir -p "$HOOK_DIR"
  sed "s|__MONTREK_DIR__|$REPO_DIR|" \
      "$REPO_DIR/bin/server/letsencrypt-deploy-hook.sh" > "$HOOK_DIR/$HOOK_NAME"
  chmod +x "$HOOK_DIR/$HOOK_NAME"
  green "Installed deploy hook: $HOOK_DIR/$HOOK_NAME"
fi

# --- tell the operator what to put in .env -------------------------------------
cat <<EOF

Add these lines to $REPO_DIR/.env (this script does not edit it):

  TLS_CERT_DIR=/etc/letsencrypt
  SSL_CERT_PATH=/etc/tls/live/$BEST/fullchain.pem
  SSL_KEY_PATH=/etc/tls/live/$BEST/privkey.pem

Then apply and verify:

  docker compose build nginx && docker compose up -d nginx
  docker compose logs nginx | grep serving
  sudo certbot renew --dry-run

EOF
