#!/bin/bash

# Script to clean up unused Docker artifacts
echo "Starting Docker cleanup..."

# Remove stopped containers
echo "Removing stopped containers..."
docker container prune -f

# Remove unused images
echo "Removing unused images..."
docker image prune -a -f

# Remove unused networks
echo "Removing unused networks..."
docker network prune -f

# Clear build caches
echo "Clearing build caches..."
docker builder prune -f

# Don't remove unused volumes as a precaution,
# since deleting volumes can lead to data loss.

echo "Docker cleanup completed!"
