#!/bin/sh

# Required env (fail fast with a clear message if any are missing)
: "${KEYCLOAK_REALM:?Set KEYCLOAK_REALM in .env}"
: "${KEYCLOAK_CLIENT_ID:?Set KEYCLOAK_CLIENT_ID in .env}"
: "${PROJECT_NAME:?Set PROJECT_NAME in .env}"
: "${DEPLOY_HOST:?Set DEPLOY_HOST in .env}"

IMPORT_DIR="/opt/keycloak/data/import"
mkdir -p "$IMPORT_DIR"

# You can override REDIRECT_URI if needed; otherwise we derive it
REDIRECT_URI="${REDIRECT_URI:-https://${PROJECT_NAME}.${DEPLOY_HOST}/*}"

# Match the login theme colors to the Django app's PRIMARY_COLOR/SECONDARY_COLOR
PRIMARY_COLOR="${PRIMARY_COLOR:-#004767}"
SECONDARY_COLOR="${SECONDARY_COLOR:-#BE0D3E}"
THEME_CSS_DIR="/opt/keycloak/themes/montrek/login/resources/css"
if [ -d "$THEME_CSS_DIR" ]; then
  cat >"${THEME_CSS_DIR}/colors.css" <<CSS
/* Generated from PRIMARY_COLOR/SECONDARY_COLOR in .env by init-realm.sh */
:root {
  --mt-accent: ${PRIMARY_COLOR};
  --mt-secondary: ${SECONDARY_COLOR};
}
CSS
fi

# Write the realm import JSON (public client, no secret)
cat >"${IMPORT_DIR}/realm.json" <<JSON
{
  "realm": "${KEYCLOAK_REALM}",
  "enabled": true,
  "loginTheme": "montrek",
  "requiredActions": [
    {
      "alias": "CONFIGURE_TOTP",
      "name": "Configure OTP",
      "providerId": "CONFIGURE_TOTP",
      "enabled": true,
      "defaultAction": true,
      "priority": 10,
      "config": {}
    },
    {
      "alias": "UPDATE_PASSWORD",
      "name": "Update Password",
      "providerId": "UPDATE_PASSWORD",
      "enabled": true,
      "defaultAction": true,
      "priority": 20,
      "config": {}
    }
  ],
  "clients": [
    {
      "clientId": "${KEYCLOAK_CLIENT_ID}",
      "protocol": "openid-connect",
      "publicClient": false,
      "redirectUris": ["${REDIRECT_URI}"],
      "attributes": { "pkce.code.challenge.method": "S256" }
    }
  ],
  "users": [
    {
      "username": "django-admin",
      "enabled": true,
      "email": "${ADMIN_EMAIL}",
      "emailVerified": true,
      "firstName": "Admin",
      "lastName":  "Django",
      "requiredActions": ["CONFIGURE_TOTP"],
      "credentials": [
        { "type": "password", "value": "${KEYCLOAK_ADMIN_PASSWORD}", "temporary": false }
      ]
    }
  ]
}
JSON
# Start Keycloak and import if realm doesn't already exist in DB
exec /opt/keycloak/bin/kc.sh start --import-realm
