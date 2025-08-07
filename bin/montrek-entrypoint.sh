#!/bin/bash
set -e
echo "SERVICE is: $SERVICE"

# Install instance-specific certs if provided
if [[ -f /certs/fullchain.crt ]]; then
  echo "Installing instance-specific certificate..."
  cp /certs/fullchain.crt /usr/local/share/ca-certificates/montrek_root_ca.crt
  update-ca-certificates
fi
# Conditionally run the app as appuser only for the "web" role
if [[ "$SERVICE" == "web" ]]; then
  echo "Running web logic as appuser..."
  exec /montrek/bin/web-entrypoint.sh
else
  echo "Skipping appuser switch for role: $SERVICE"
  exec "$@" # Or run default logic for other services
fi
