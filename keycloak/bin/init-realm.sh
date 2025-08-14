#!/bin/sh
set -euo pipefail

# Required env (fail fast with a clear message if any are missing)
: "${KEYCLOAK_REALM:?Set KEYCLOAK_REALM in .env}"
: "${KEYCLOAK_CLIENT_ID:?Set KEYCLOAK_CLIENT_ID in .env}"
: "${PROJECT_NAME:?Set PROJECT_NAME in .env}"
: "${DEPLOY_HOST:?Set DEPLOY_HOST in .env}"

IMPORT_DIR="/opt/keycloak/data/import"
mkdir -p "$IMPORT_DIR"

# You can override REDIRECT_URI if needed; otherwise we derive it
REDIRECT_URI="${REDIRECT_URI:-https://${PROJECT_NAME}.${DEPLOY_HOST}/*}"

# Write the realm import JSON (public client, no secret)
cat >"${IMPORT_DIR}/realm.json" <<JSON
{
  "realm": "${KEYCLOAK_REALM}",
  "enabled": true,
  "clients": [
    {
      "clientId": "${KEYCLOAK_CLIENT_ID}",
      "protocol": "openid-connect",
      "publicClient": true,
      "redirectUris": ["${REDIRECT_URI}"],
      "attributes": { "pkce.code.challenge.method": "S256" }
    }
  ]
}
JSON
# Start Keycloak and import if realm doesn't already exist in DB
exec /opt/keycloak/bin/kc.sh start --import-realm
