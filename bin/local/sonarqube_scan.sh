#!/bin/bash

# Load variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found!"
  exit 1
fi
# Check if required variables are set
missing_vars=()

if [[ -z "$SONARCUBE_URL" ]]; then
  missing_vars+=("SONARCUBE_URL")
fi

if [[ -z "$SONARCUBE_TOKEN" ]]; then
  missing_vars+=("SONARCUBE_TOKEN")
fi

if [[ ${#missing_vars[@]} -ne 0 ]]; then
  echo "One or more required environment variables are missing in .env:"
  for var in "${missing_vars[@]}"; do
    echo "$var"
  done
  exit 1
fi
RUN_TESTS=true
REPO=montrek
for arg in "$@"; do
  if [[ "$arg" == "NO_TESTS=true" ]]; then
    RUN_TESTS=false
  elif [[ "$arg" == "NO_TESTS=" ]]; then
    RUN_TESTS=true
  elif [[ "$arg" == "NO_TESTS=false" ]]; then
    RUN_TESTS=true
  else
    REPO=$arg
  fi
done
echo "Analysing repository $REPO..."

if [[ "$REPO" == "montrek" ]]; then
  cd montrek/
else
  cd montrek/$REPO
fi

if $RUN_TESTS; then
  if [[ "$REPO" == "montrek" ]]; then
    echo "Running tests (excluding subrepos)..."
    # Get all subdirs containing __init__.py (i.e. Python packages)
    all_apps=$(find . -type f -name '__init__.py' -exec dirname {} \; | sort -u)

    # Find subdirs that are separate Git repos
    subrepos=$(find . -type d -name ".git" | sed 's|/.git||')

    # Filter out subrepos from the list of apps
    apps_to_test=()
    for app in $all_apps; do
      skip=false
      for repo in $subrepos; do
        if [[ "$app" == "$repo"* ]]; then
          skip=true
          break
        fi
      done
      if ! $skip; then
        # Normalize to Django dot-style import path
        app_path=$(echo "$app" | sed 's|^\./||' | tr '/' '.')
        apps_to_test+=("$app_path")
      fi
    done

    # Now run Django tests only on those apps
    coverage run --rcfile=../.coveragerc manage.py test "${apps_to_test[@]}" --keepdb --parallel
  else
    coverage run --rcfile=.coveragerc ../manage.py test --keepdb --parallel
  fi
  coverage combine
  coverage xml -o coverage.xml
else
  echo "Skip running tests"
fi
if [[ "$REPO" == "montrek" ]]; then
  mv coverage.xml ../
  cd ../
fi

sonar-scanner -Dsonar.projectKey=$REPO -Dsonar.sources=. -Dsonar.exclusions=**/migrations/**,**/static/** -Dsonar.host.url=$SONARCUBE_URL -Dsonar.login=$SONARCUBE_TOKEN -Dsonar.python.coverage.reportPaths=coverage.xml | grep "ANALYSIS SUCCESSFUL"
