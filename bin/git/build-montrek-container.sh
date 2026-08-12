#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=".env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo ".env file not found!"
  exit 1
fi

# Load variables from .env. Using `source` (instead of `export $(... | xargs)`)
# so that values containing spaces or commas are kept intact.
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

missing=()
[[ -n "${GIT_USER:-}" ]] || missing+=("GIT_USER")
[[ -n "${GIT_PAT:-}" ]] || missing+=("GIT_PAT")
if [[ ${#missing[@]} -gt 0 ]]; then
  echo "One or more required environment variables are missing in $ENV_FILE:"
  printf '  %s\n' "${missing[@]}"
  exit 1
fi

CONTAINER_REGISTRY="${CONTAINER_REGISTRY:-ghcr.io}"
CONTAINER_NAMESPACE="${CONTAINER_NAMESPACE:-montrek-software}"
CONTAINER_IMAGE="${CONTAINER_IMAGE:-montrek-container}"
CONTAINER_TAG="${CONTAINER_TAG:-latest}"

IMAGE="${CONTAINER_REGISTRY}/${CONTAINER_NAMESPACE}/${CONTAINER_IMAGE}:${CONTAINER_TAG}"

echo "🔑 Logging in to ${CONTAINER_REGISTRY} as ${GIT_USER}..."
printf '%s' "$GIT_PAT" | docker login "$CONTAINER_REGISTRY" --username "$GIT_USER" --password-stdin

echo "🐳 Building ${IMAGE}..."
docker build -t "$IMAGE" .

echo "⬆️  Pushing ${IMAGE}..."
docker push "$IMAGE"

echo "✅ Done: ${IMAGE}"
