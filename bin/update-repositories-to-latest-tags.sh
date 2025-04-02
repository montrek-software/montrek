#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to update a git repository to the latest tag
update_repo_to_latest_tag() {
  local repo_path="$1"
  echo "Updating repository at: $repo_path"
  cd "$repo_path"

  # Fetch all tags
  git fetch --tags

  # Get the latest tag
  latest_tag=$(git describe --tags $(git rev-list --tags --max-count=1) 2>/dev/null || true)

  if [ -n "$latest_tag" ]; then
    echo "Checking out to latest tag: $latest_tag"
    git checkout "$latest_tag"
  else
    echo "No tags found in repository: $repo_path"
  fi

  # Return to the original directory
  cd - >/dev/null
}

# Find all git repositories and update them
find . -type d -name ".git" | while read git_dir; do
  repo_path=$(dirname "$git_dir")
  update_repo_to_latest_tag "$repo_path"
done

echo "All repositories have been updated to the latest tags."
