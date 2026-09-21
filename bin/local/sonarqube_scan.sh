#!/bin/bash

# Configuration comes from the environment first and only then from .env, so
# this works unchanged on the host and inside a container where .env is
# deliberately shadowed.
# shellcheck source=../lib/load-env.sh
. "$(dirname "${BASH_SOURCE[0]}")/../lib/load-env.sh"
# The analysis token is a CI credential, so .env.build takes precedence
# over the runtime .env.
montrek_load_env .env.build
montrek_load_env
montrek_require_env SONARCUBE_URL SONARCUBE_TOKEN || exit 1
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

# The scan runs one level above the tests for montrek itself -- sonar.sources
# covers the whole repository -- and in the subrepo directory otherwise. The
# report has to land where the scan runs, because sonar.python.coverage
# .reportPaths is resolved against sonar.projectBaseDir.
PROJECT_ROOT="$PWD"
COVERAGE_RC="$PROJECT_ROOT/montrek/.coveragerc"
if [[ "$REPO" == "montrek" ]]; then
  COVERAGE_DIR="$PROJECT_ROOT/montrek"
  SCAN_DIR="$PROJECT_ROOT"
else
  COVERAGE_DIR="$PROJECT_ROOT/montrek/$REPO"
  SCAN_DIR="$COVERAGE_DIR"
fi
COVERAGE_XML="$SCAN_DIR/coverage.xml"

cd "$COVERAGE_DIR" || exit 1

if $RUN_TESTS; then
  # A report that cannot be written must not leave the previous one behind:
  # sonar-scanner would happily upload it and report an old figure as today's.
  rm -f "$COVERAGE_XML"
  # Parts left over from a run that was interrupted would be combined into this
  # run's data and reported as if they belonged to it.
  coverage erase --rcfile="$COVERAGE_RC"

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
    coverage run --rcfile="$COVERAGE_RC" manage.py test "${apps_to_test[@]}" --parallel
  else
    coverage run --rcfile="$COVERAGE_RC" "$PROJECT_ROOT/montrek/manage.py" test --parallel
  fi
  test_status=$?
  # Failing tests still leave usable data, so the scan goes ahead -- but the
  # coverage it reports is the coverage of a run that did not finish cleanly.
  if ((test_status != 0)); then
    echo "Warning: the test run exited with status $test_status; coverage below is from an incomplete run." >&2
  fi

  # Both steps are silent killers: coverage.py aborts the whole XML report over
  # a single measured file whose source has gone (a test fixture generated and
  # then deleted, say), and without an explicit check the scan continues with no
  # report at all.
  if ! coverage combine --rcfile="$COVERAGE_RC"; then
    echo "Error: 'coverage combine' failed; no coverage report was produced." >&2
    exit 1
  fi
  if ! coverage xml --rcfile="$COVERAGE_RC" -o "$COVERAGE_XML"; then
    echo "Error: 'coverage xml' failed; no coverage report was produced." >&2
    echo "A measured file whose source no longer exists aborts the report -- add it to 'omit' in $COVERAGE_RC." >&2
    exit 1
  fi
else
  echo "Skip running tests"
fi

cd "$SCAN_DIR" || exit 1

if [[ -f "coverage.xml" ]]; then
  echo "Coverage report: $COVERAGE_XML (written $(date -r "coverage.xml" '+%Y-%m-%d %H:%M'))"
else
  echo "Warning: no $COVERAGE_XML -- this scan reports no coverage at all." >&2
fi

# The scanner's own warnings are the only sign that a report was found but not
# used ("Fail to resolve ... file(s)"), so keep the log and show them rather
# than piping everything into grep, which used to hide them and replace the
# scanner's exit status with grep's.
SCAN_LOG="$(mktemp -t "sonar-scan-$REPO-XXXXXX.log")"
sonar-scanner \
  -Dsonar.projectKey="$REPO" \
  -Dsonar.sources=. \
  -Dsonar.exclusions=**/migrations/**,**/static/**,**/scripts/** \
  -Dsonar.cpd.exclusions=**/tests/** \
  -Dsonar.host.url="$SONARCUBE_URL" \
  -Dsonar.login="$SONARCUBE_TOKEN" \
  -Dsonar.python.coverage.reportPaths=coverage.xml \
  >"$SCAN_LOG" 2>&1
scan_status=$?

grep -E "Fail to resolve|No coverage|coverage report|WARN" "$SCAN_LOG" | head -20

if ((scan_status != 0)); then
  echo "Error: sonar-scanner failed with status $scan_status." >&2
  tail -20 "$SCAN_LOG" >&2
  echo "Full scanner log: $SCAN_LOG" >&2
  exit "$scan_status"
fi

grep "ANALYSIS SUCCESSFUL" "$SCAN_LOG"
echo "Full scanner log: $SCAN_LOG"
