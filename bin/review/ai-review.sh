#!/usr/bin/env bash
# Review the current branch of core or of one extension with an LLM.
#
# Configuration comes from the environment (make variables, CI) or .env:
#   AI_REVIEW_PROVIDER  mistral (default) or ionos
#   MISTRAL_API_KEY     for mistral; IONOS_API_TOKEN for ionos
#   AI_REVIEW_MODEL     default mistral-large-4 / Qwen/Qwen3-Coder-Next
#                       (MISTRAL_MODEL still works for mistral)
#   AI_REVIEW_PRICE_INPUT / _OUTPUT
#                       price per million tokens, for the cost estimate
#   REPO                montrek (default) or an mt_* extension under montrek/
#   BASE                target branch, default origin/main (run git fetch first)
#   WORKTREE=true       include uncommitted changes to tracked files
#   TESTS=true          run the touched apps' tests and measure patch coverage
#   COVERAGE_XML        use an existing coverage.xml instead of running tests
#   OUTPUT              write the review to this file instead of stdout
#   DRY_RUN=true        print the prompt and stop, without calling the API
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
[[ "${TESTS:-}" == true ]] && args+=(--run-tests)
[[ -n "${COVERAGE_XML:-}" ]] && args+=(--coverage-xml "$COVERAGE_XML")
[[ -n "${OUTPUT:-}" ]] && args+=(--output "$OUTPUT")
# The API key is checked by the provider, which knows its variable name.
[[ "${DRY_RUN:-}" == true ]] && args+=(--dry-run)

exec "${PYTHON:-python3}" "$SCRIPT_DIR/ai_review.py" "${args[@]}" "$@"
