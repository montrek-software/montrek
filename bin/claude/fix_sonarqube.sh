#!/bin/bash
# fetch_sonar_and_fix.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load variables from .env file
if [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
else
  echo ".env file not found!" >&2
  exit 1
fi

missing_vars=()

if [[ -z "$SONARCUBE_URL" ]]; then
  missing_vars+=("SONARCUBE_URL")
fi

if [[ -z "$SONARCUBE_TOKEN" ]]; then
  missing_vars+=("SONARCUBE_TOKEN")
fi

if [[ ${#missing_vars[@]} -gt 0 ]]; then
  echo "Error: missing required environment variables: ${missing_vars[*]}" >&2
  exit 1
fi

REPO="${1:-montrek}"
SONARCUBE_URL="${SONARCUBE_URL%/}"  # strip trailing slash

echo "Fetching SonarQube issues for project '$REPO' from $SONARCUBE_URL ..."

http_code=$(curl -s -o /tmp/sonar_response.json -w "%{http_code}" -u "$SONARCUBE_TOKEN:" \
  "$SONARCUBE_URL/api/issues/search?componentKeys=$REPO&statuses=OPEN,CONFIRMED&inNewCodePeriod=true&ps=500")

if [[ "$http_code" -eq 401 ]]; then
  echo "Error: SonarQube authentication failed (HTTP 401). Check SONARCUBE_TOKEN." >&2
  exit 1
elif [[ "$http_code" -eq 403 ]]; then
  echo "Error: SonarQube access denied (HTTP 403). Token lacks permission for project '$REPO'." >&2
  exit 1
elif [[ "$http_code" -eq 404 ]]; then
  echo "Error: SonarQube project '$REPO' not found (HTTP 404). Check SONARCUBE_URL and project key." >&2
  exit 1
elif [[ "$http_code" -lt 200 || "$http_code" -ge 300 ]]; then
  echo "Error: SonarQube request failed with HTTP $http_code." >&2
  echo "Response: $(cat /tmp/sonar_response.json)" >&2
  exit 1
fi

response=$(cat /tmp/sonar_response.json)
issue_count=$(echo "$response" | python3 -c "import json,sys; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null || echo "?")
echo "Found $issue_count open issue(s) in new code period."

if [[ "$issue_count" == "0" ]]; then
  echo "No issues to fix."
  exit 0
fi

issues=$(echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for issue in data.get('issues', []):
    print(json.dumps({
        'severity': issue.get('severity', '?'),
        'rule':     issue.get('rule', '?'),
        'file':     issue.get('component', '?').split(':', 1)[-1],
        'line':     str(issue.get('line', '?')),
        'message':  issue.get('message', '?'),
    }))
")

total=$(echo "$issues" | wc -l)
current=0
approve_all=false

while IFS= read -r issue_json; do
  current=$((current + 1))
  severity=$(echo "$issue_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['severity'])")
  rule=$(echo "$issue_json"     | python3 -c "import json,sys; print(json.load(sys.stdin)['rule'])")
  file=$(echo "$issue_json"     | python3 -c "import json,sys; print(json.load(sys.stdin)['file'])")
  line=$(echo "$issue_json"     | python3 -c "import json,sys; print(json.load(sys.stdin)['line'])")
  message=$(echo "$issue_json"  | python3 -c "import json,sys; print(json.load(sys.stdin)['message'])")

  echo ""
  echo "════════════════════════════════════════════════════════"
  echo "  Issue $current / $total  [$severity]  $rule"
  echo "  File:    $file:$line"
  echo "  Message: $message"
  echo "════════════════════════════════════════════════════════"

  if [[ "$approve_all" == false ]]; then
    read -rp "  [f]ix / [s]kip / [a]pprove all? " choice < /dev/tty
    case "$choice" in
      s|S) echo "  Skipping."; continue ;;
      a|A) approve_all=true ;;
    esac
  fi

  if [[ "$REPO" != "montrek" ]]; then
    full_path="$REPO/$file"
  else
    full_path="$file"
  fi

  claude --verbose "Fix this SonarQube issue in the codebase of $REPO:

[$severity] $rule in $full_path:$line
  $message" < /dev/null

done <<< "$issues"

make -C "$PROJECT_ROOT" local-sonarqube-scan
