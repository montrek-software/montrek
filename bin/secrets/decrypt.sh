#!/bin/bash
set -e

ENV_FILE=".env"
MARKER_FILE=".env.encrypted"

usage() {
  echo "Usage: $0 [--echo-password]" >&2
  echo "  --echo-password   Print the entered password to stdout (for automation)" >&2
  exit 1
}

ECHO_PASSWORD=false
if [[ "$1" == "--echo-password" ]]; then
  ECHO_PASSWORD=true
elif [[ -n "$1" ]]; then
  usage
fi

# Check if the marker file exists
if [[ ! -f "$MARKER_FILE" ]]; then
  echo "ℹ️  $ENV_FILE is not encrypted (no marker file found)." >&2
  if $ECHO_PASSWORD; then
    echo ""
  fi
  exit 0
fi

# Check if .env exists
if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌  $ENV_FILE not found, cannot decrypt." >&2
  exit 1
fi

# Ask for password (input hidden)
echo -n "🔑 Enter Ansible Vault password: " >&2
read -s VAULT_PASS
echo >&2

# Create a temporary password file
VAULT_PASS_FILE=$(mktemp)
echo "$VAULT_PASS" >"$VAULT_PASS_FILE"

# Decrypt the .env file
if ansible-vault decrypt "$ENV_FILE" --vault-password-file "$VAULT_PASS_FILE" >&2; then
  echo "✅  $ENV_FILE decrypted successfully." >&2
else
  echo "❌  Decryption failed." >&2
  shred -u "$VAULT_PASS_FILE"
  exit 1
fi

# Clean up
shred -u "$VAULT_PASS_FILE"

# Remove marker file
rm -f "$MARKER_FILE"
echo "🧹  Marker file removed: $MARKER_FILE" >&2

# Only print password (to stdout) for automation
if $ECHO_PASSWORD; then
  echo "$VAULT_PASS"
fi
