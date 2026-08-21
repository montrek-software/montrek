#!/bin/bash
# Report the certificate nginx is actually serving, and how long it has left.
# The failure this guards against is nobody noticing an expiry for months.
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_DIR"

echo "--- configured in the container ---"
docker compose exec -T nginx sh -c '
  echo "SSL_CERT_PATH=$SSL_CERT_PATH"
  openssl x509 -noout -subject -enddate -in "$SSL_CERT_PATH"
' 2>/dev/null || echo "nginx container not running"

HOST=$(grep -E '^PROJECT_NAME=' .env | cut -d= -f2-).$(grep -E '^DEPLOY_HOST=' .env | cut -d= -f2-)
echo
echo "--- actually served on $HOST ---"
if end=$(echo | timeout 15 openssl s_client -connect "$HOST:443" -servername "$HOST" 2>/dev/null \
         | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2); then
  days=$(( ( $(date -d "$end" +%s) - $(date +%s) ) / 86400 ))
  echo "expires: $end  (${days} days)"
  [[ $days -lt 21 ]] && echo "WARNING: fewer than 21 days remaining"
else
  echo "could not reach $HOST:443"
fi
