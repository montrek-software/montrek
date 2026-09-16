#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=../lib/load-env.sh
. "$(dirname "${BASH_SOURCE[0]}")/../lib/load-env.sh"

# Registry push credentials live in .env.build, not .env: .env is handed to
# every app container via `env_file:`, and a registry write token there turns
# an application compromise into a supply-chain one. .env is still read as a
# fallback so existing checkouts keep working.
montrek_load_env .env.build
montrek_load_env .env

# Rebuilding for a local restart needs no registry credentials, and the push
# creds now live in .env.build rather than .env, so requiring them
# unconditionally would block the common case.
PUSH=true
for arg in "$@"; do
  case "$arg" in
  --no-push) PUSH=false ;;
  *)
    echo "Unknown argument: $arg" >&2
    echo "Usage: $0 [--no-push]" >&2
    exit 1
    ;;
  esac
done

if $PUSH; then
  montrek_require_env GIT_USER GIT_PAT || exit 1
fi

CONTAINER_REGISTRY="${CONTAINER_REGISTRY:-ghcr.io}"
CONTAINER_NAMESPACE="${CONTAINER_NAMESPACE:-montrek-software}"
CONTAINER_IMAGE="${CONTAINER_IMAGE:-montrek-container}"
CONTAINER_TAG="${CONTAINER_TAG:-latest}"

IMAGE="${CONTAINER_REGISTRY}/${CONTAINER_NAMESPACE}/${CONTAINER_IMAGE}:${CONTAINER_TAG}"

if $PUSH; then
  echo "🔑 Logging in to ${CONTAINER_REGISTRY} as ${GIT_USER}..."
  printf '%s' "$GIT_PAT" | docker login "$CONTAINER_REGISTRY" --username "$GIT_USER" --password-stdin
fi

echo "🐳 Building ${IMAGE}..."
docker build -t "$IMAGE" .

if $PUSH; then
  echo "⬆️  Pushing ${IMAGE}..."
  docker push "$IMAGE"
else
  echo "⏭️  Skipping push (--no-push); the local tag is what compose uses."
fi

echo "✅ Done: ${IMAGE}"
