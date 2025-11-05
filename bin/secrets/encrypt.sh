#!/bin/bash
set -e

ENV_FILE=".env"
MARKER_FILE=".env.encrypted"

# Check if already encrypted
if [[ -f "$MARKER_FILE" ]]; then
  echo "⚠️  $ENV_FILE is already encrypted."
  exit 0
fi

# Check if env file exists
if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌  $ENV_FILE not found."
  exit 1
fi

# If password passed as first argument, use it; otherwise generate one
if [[ -n "$1" ]]; then
  VAULT_PASS="$1"
  echo "🔐 Using provided Ansible Vault password."
else
  VAULT_PASS=$(openssl rand -hex 32)
  echo "🔑 Generated Ansible Vault password (SAVE THIS SAFELY):"
  echo "$VAULT_PASS"
  echo
fi

# Create a temporary password file
VAULT_PASS_FILE=$(mktemp)
echo "$VAULT_PASS" >"$VAULT_PASS_FILE"

# Encrypt the .env file
ansible-vault encrypt "$ENV_FILE" --vault-password-file "$VAULT_PASS_FILE"

# Create a marker file
touch "$MARKER_FILE"

# Clean up
shred -u "$VAULT_PASS_FILE"

echo "✅  $ENV_FILE encrypted successfully."
echo "📄  Marker file created: $MARKER_FILE"
