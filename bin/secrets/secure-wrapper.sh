#!/usr/bin/env bash
set -euo pipefail

DECRYPT_SCRIPT="./bin/secrets/decrypt.sh"
ENCRYPT_SCRIPT="./bin/secrets/encrypt.sh"
ENV_FILE=".env"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <script_to_run> [args...]"
  exit 1
fi

CHILD_SCRIPT="$1"
shift

# Decrypt .env and capture password while showing output
ENCRYPT_PASSWORD="$("$DECRYPT_SCRIPT" --echo-password > >(tee /dev/tty))"

# Ensure re-encryption happens even if something fails
cleanup() {
  echo "🔐 Re-encrypting $ENV_FILE..."
  "$ENCRYPT_SCRIPT" "$ENCRYPT_PASSWORD"
}
trap cleanup EXIT

# Run the wrapped command/script
(
  "$CHILD_SCRIPT" "$@"
)
