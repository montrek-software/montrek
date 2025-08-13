#!/usr/bin/env bash
set -euo pipefail

# Tunables (override via env): e.g. UNTIL="24h" KEEP_STORAGE="10GB"
UNTIL="${UNTIL:-24h}"                # only delete cache older than this
KEEP_STORAGE="${KEEP_STORAGE:-10GB}" # keep at least this much cache
TIMEOUT_SECS="${TIMEOUT_SECS:-300}"  # bound the prune step

echo "Starting Docker cleanup..."

# Quick sanity: is the daemon up?
if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon not available. Skipping."
  exit 0
fi

echo "Removing stopped containers..."
docker container prune -f

echo "Removing dangling/unused images..."
docker image prune -a -f

echo "Removing unused networks..."
docker network prune -f

# Build cache
# Use age filter + keep-storage, and cap runtime with timeout.
echo "Pruning BuildKit cache (older than ${UNTIL}, keep ${KEEP_STORAGE})..."
if command -v timeout >/dev/null 2>&1; then
  timeout "${TIMEOUT_SECS}s" docker builder prune -f -a \
    --filter "until=${UNTIL}" \
    --keep-storage "${KEEP_STORAGE}" || echo "builder prune skipped/timed out"
else
  docker builder prune -f -a \
    --filter "until=${UNTIL}" \
    --keep-storage "${KEEP_STORAGE}"
fi

echo "After cleanup:"
docker system df || true

echo "Docker cleanup completed!"
