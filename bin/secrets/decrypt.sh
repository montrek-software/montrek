#!/bin/bash
set -e

ENV_FILE=".env"
MARKER_FILE=".env.encrypted"

# Check if the marker file exists
if [[ ! -f "$MARKER_FILE" ]]; then
  echo "ℹ️  $ENV_FILE is not encrypted (no marker file found)."
  exit 0
fi

# Check if .env exists
if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌  $ENV_FILE not found, cannot decrypt."
  exit 1
fi

# Require vault password
if [[ -z "$1" ]]; then
  echo "❌  No Ansible Vault password provided."
  echo "Usage: $0 <vault_password>"
  exit 1
fi

VAULT_PASS="$1"

# Create a temporary password file
VAULT_PASS_FILE=$(mktemp)
echo "$VAULT_PASS" >"$VAULT_PASS_FILE"

# Decrypt the .env file
ansible-vault decrypt "$ENV_FILE" --vault-password-file "$VAULT_PASS_FILE"

# Clean up
shred -u "$VAULT_PASS_FILE"

# Remove marker file
rm -f "$MARKER_FILE"

echo "✅  $ENV_FILE decrypted successfully."
echo "🧹  Marker file removed: $MARKER_FILE"
