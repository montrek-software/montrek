#!/usr/bin/env bash
set -euo pipefail

# Preflight for `make git-build-montrek-container`. Separates the three ways a
# push gets rejected, which docker's own "unauthorized" does not distinguish:
#
#   1. the wrong registry host (credentials are fine, aimed at the wrong place)
#   2. bad credentials (wrong user, expired or revoked token)
#   3. valid credentials without write:package on the target repository
#
# shellcheck source=../lib/load-env.sh
. "$(dirname "${BASH_SOURCE[0]}")/../lib/load-env.sh"
montrek_load_env .env.build
montrek_load_env .env
montrek_require_env GIT_USER GIT_PAT || exit 1

REGISTRY="${CONTAINER_REGISTRY:-ghcr.io}"
NAMESPACE="${CONTAINER_NAMESPACE:-montrek-software}"
IMAGE_NAME="${CONTAINER_IMAGE:-montrek-container}"
REPO="${NAMESPACE}/${IMAGE_NAME}"

echo "Registry : ${REGISTRY}"
echo "Repository: ${REPO}"
echo "User     : ${GIT_USER}"
echo

echo "[1/3] Registry reachable and speaking the v2 API..."
realm="$(curl -fsS -m 20 -D - -o /dev/null "https://${REGISTRY}/v2/" 2>/dev/null |
  tr -d '\r' | awk -F'"' 'tolower($0) ~ /^www-authenticate/ {print $2}')" || true
if [[ -z "$realm" ]]; then
  # A 200 with no challenge means an open registry; anything else is a problem.
  code="$(curl -s -o /dev/null -m 20 -w '%{http_code}' "https://${REGISTRY}/v2/" || echo 000)"
  if [[ "$code" == "200" ]]; then
    echo "      OK (no authentication required)"
    exit 0
  fi
  echo "      FAILED: no Bearer challenge from https://${REGISTRY}/v2/ (HTTP ${code})."
  echo "      Check CONTAINER_REGISTRY -- it must be the HOST only, no path."
  exit 1
fi
echo "      OK (token realm: ${realm})"

echo "[2/3] Credentials accepted..."
scope="repository:${REPO}:pull,push"
body="$(curl -s -m 20 -o /tmp/mt-token.$$ -w '%{http_code}' \
  --user "${GIT_USER}:${GIT_PAT}" \
  "${realm}?service=container_registry&scope=${scope}")" || true
token="$(python3 -c "
import json,sys
try: print(json.load(open('/tmp/mt-token.$$')).get('token',''))
except Exception: print('')
")"
rm -f "/tmp/mt-token.$$"

if [[ "$body" != "200" || -z "$token" ]]; then
  echo "      FAILED: HTTP ${body} from the token endpoint."
  echo "      The user or token is wrong, expired or revoked."
  echo "      For Forgejo, GIT_USER is the login name (not an email) and"
  echo "      GIT_PAT an access token with the write:package scope."
  exit 1
fi
echo "      OK"

echo "[3/3] Token grants push on ${REPO}..."
granted="$(python3 - "$token" <<'PY'
import base64, json, sys
payload = sys.argv[1].split('.')[1]
payload += '=' * (-len(payload) % 4)
access = json.loads(base64.urlsafe_b64decode(payload)).get('access') or []
print(';'.join(f"{a.get('name')}={','.join(a.get('actions') or [])}" for a in access))
PY
)"
if [[ -z "$granted" ]]; then
  echo "      FAILED: authenticated, but granted no rights on ${REPO}."
  echo "      The token lacks write:package, or ${GIT_USER} has no write access"
  echo "      to the '${NAMESPACE}' owner/organisation."
  exit 1
fi
echo "      granted: ${granted}"
case "$granted" in
*push*) echo; echo "Ready to push: ${REGISTRY}/${REPO}:${CONTAINER_TAG:-latest}" ;;
*)
  echo "      FAILED: pull only, no push."
  exit 1
  ;;
esac
