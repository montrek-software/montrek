#!/usr/bin/env bash
# Check the current branch of core or of one extension against the mechanical
# criteria of CONTRIBUTION_CRITERIA.md (see docs/contribution_check.md).
#
# Configuration comes from the environment (make variables, CI) or .env:
#   REPO              montrek (default) or an mt_* extension under montrek/
#   BASE              target branch, default origin/main (run git fetch first)
#   WORKTREE=true     include uncommitted changes to tracked files
#   COVERAGE_XML      coverage report for the patch coverage (M6)
#   SKIP_PRE_COMMIT=true
#                     skip pre-commit; it otherwise runs, and its hooks may fix
#                     files in place, as on a commit
#   OUTPUT            write the report to this file instead of stdout
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=../lib/load-env.sh
. "$SCRIPT_DIR/../lib/load-env.sh"
cd "$PROJECT_ROOT"
montrek_load_env

args=()
[[ -n "${REPO:-}" ]] && args+=(--repo "$REPO")
[[ -n "${BASE:-}" ]] && args+=(--base "$BASE")
[[ "${WORKTREE:-}" == true ]] && args+=(--worktree)
[[ -n "${COVERAGE_XML:-}" ]] && args+=(--coverage-xml "$COVERAGE_XML")
[[ "${SKIP_PRE_COMMIT:-}" == true ]] && args+=(--skip-pre-commit)
[[ -n "${OUTPUT:-}" ]] && args+=(--output "$OUTPUT")

exec "${PYTHON:-python3}" "$SCRIPT_DIR/contribution_check.py" "${args[@]}" "$@"
