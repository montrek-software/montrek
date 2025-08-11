#!/bin/bash
set -e
echo "SERVICE is: $SERVICE"

if [[ -f /montrek/nginx/certs/fullchain.crt ]]; then
  echo "Installing instance-specific certificate system-wide..."
  cp /montrek/nginx/certs/fullchain.crt /usr/local/share/ca-certificates/montrek_root_ca.crt
  update-ca-certificates
fi
