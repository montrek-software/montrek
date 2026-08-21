#!/bin/bash
# Certbot deploy hook: reload nginx after a certificate is renewed.
#
# Certbot runs every executable in /etc/letsencrypt/renewal-hooks/deploy/ after a
# successful renewal. nginx serves the certificate from a read-only mount of
# /etc/letsencrypt, so it only needs a graceful reload to pick up the new file --
# in-flight requests finish on the old workers, so there is no downtime.
#
# Installed as a symlink by `make server-enable-letsencrypt`.
set -euo pipefail

MONTREK_DIR="${MONTREK_DIR:-__MONTREK_DIR__}"

log() { logger -t montrek-tls "$*" 2>/dev/null || true; echo "montrek-tls: $*"; }

cd "$MONTREK_DIR" || { log "ERROR: $MONTREK_DIR not found"; exit 1; }

if ! docker compose ps --status running --services 2>/dev/null | grep -qx nginx; then
  log "nginx container not running; nothing to reload"
  exit 0
fi

# Validate before reloading: a reload with a broken config leaves the old
# workers serving, but we want the failure reported rather than swallowed.
if ! docker compose exec -T nginx nginx -t; then
  log "ERROR: nginx config test failed, not reloading"
  exit 1
fi

docker compose exec -T nginx nginx -s reload
log "nginx reloaded after certificate renewal"
