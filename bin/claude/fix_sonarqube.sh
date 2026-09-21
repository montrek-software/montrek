#!/bin/bash
# fetch_sonar_and_fix.sh -- walk the open issues and the security hotspots
# SonarQube reports for the new code period and hand each one to claude.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=../lib/load-env.sh
. "$SCRIPT_DIR/../lib/load-env.sh"
montrek_load_env .env.build
montrek_load_env
montrek_require_env SONARCUBE_URL SONARCUBE_TOKEN || exit 1

REPO="${1:-montrek}"
SONARCUBE_URL="${SONARCUBE_URL%/}" # strip trailing slash

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

ISSUES_JSON="$TMP_DIR/issues.json"
HOTSPOTS_JSON="$TMP_DIR/hotspots.json"

# GET $2 into the file $1, turning the usual authentication and permission
# failures into one actionable message. A 400 comes back as exit code 2 so the
# caller can retry the same endpoint with different parameters.
sonar_get() {
  local out="$1" url="$2" http_code
  http_code=$(curl -s -o "$out" -w "%{http_code}" -u "$SONARCUBE_TOKEN:" "$url")

  case "$http_code" in
  2??) return 0 ;;
  400) return 2 ;;
  401) echo "Error: SonarQube authentication failed (HTTP 401). Check SONARCUBE_TOKEN." >&2 ;;
  403) echo "Error: SonarQube access denied (HTTP 403). Token lacks permission for project '$REPO'." >&2 ;;
  404) echo "Error: SonarQube project '$REPO' not found (HTTP 404). Check SONARCUBE_URL and project key." >&2 ;;
  *)
    echo "Error: SonarQube request failed with HTTP $http_code." >&2
    echo "Response: $(cat "$out")" >&2
    ;;
  esac
  return 1
}

# Both endpoints report the size of the full result set; only the shape differs.
sonar_total() {
  python3 -c "
import json, sys
data = json.load(open(sys.argv[1]))
print(data.get('total', data.get('paging', {}).get('total', 0)))
" "$1" 2>/dev/null || echo "?"
}

echo "Fetching SonarQube issues for project '$REPO' from $SONARCUBE_URL ..."
sonar_get "$ISSUES_JSON" \
  "$SONARCUBE_URL/api/issues/search?componentKeys=$REPO&statuses=OPEN,CONFIRMED&inNewCodePeriod=true&ps=500" ||
  exit 1

echo "Fetching SonarQube security hotspots for project '$REPO' ..."
# Hotspots live behind their own endpoint, keyed by projectKey rather than
# componentKeys, and are "to review" rather than open. inNewCodePeriod is the
# current name of the period filter; older servers only know sinceLeakPeriod and
# answer 400 for the new one, so fall back before giving up on the filter.
hotspots_url="$SONARCUBE_URL/api/hotspots/search?projectKey=$REPO&status=TO_REVIEW&ps=500"
sonar_get "$HOTSPOTS_JSON" "$hotspots_url&inNewCodePeriod=true"
case "$?" in
0) ;;
2)
  sonar_get "$HOTSPOTS_JSON" "$hotspots_url&sinceLeakPeriod=true"
  case "$?" in
  0) ;;
  2)
    echo "Note: server rejects a new code period filter for hotspots; reviewing all open ones." >&2
    sonar_get "$HOTSPOTS_JSON" "$hotspots_url" || exit 1
    ;;
  *) exit 1 ;;
  esac
  ;;
*) exit 1 ;;
esac

issue_count=$(sonar_total "$ISSUES_JSON")
hotspot_count=$(sonar_total "$HOTSPOTS_JSON")
echo "Found $issue_count open issue(s) and $hotspot_count security hotspot(s) to review."

# One tab separated row per finding, issues first, so the loop below stays a
# single pass over both kinds. Messages are flattened because the row is read
# back field by field.
mapfile -t findings < <(python3 - "$ISSUES_JSON" "$HOTSPOTS_JSON" <<'PY'
import json, sys


def flat(text, empty="?"):
    return " ".join(str(text).split()) or empty


def path_of(component):
    return str(component).split(":", 1)[-1]


rows = []
with open(sys.argv[1]) as handle:
    for issue in json.load(handle).get("issues", []):
        rows.append((
            "issue",
            issue.get("severity", "?"),
            issue.get("rule", "?"),
            path_of(issue.get("component", "?")),
            str(issue.get("line", "?")),
            flat(issue.get("message", "?")),
            "",
        ))
with open(sys.argv[2]) as handle:
    for hotspot in json.load(handle).get("hotspots", []):
        rows.append((
            "hotspot",
            hotspot.get("vulnerabilityProbability", "?"),
            hotspot.get("ruleKey", "?"),
            path_of(hotspot.get("component", "?")),
            str(hotspot.get("line", "?")),
            flat(hotspot.get("message", "?")),
            flat(hotspot.get("securityCategory", ""), empty=""),
        ))
for row in rows:
    print("\t".join(row))
PY
)

total=${#findings[@]}
if ((total == 0)); then
  echo "Nothing to fix."
  exit 0
fi

current=0
approve_all=false

for finding in "${findings[@]}"; do
  current=$((current + 1))
  IFS=$'\t' read -r kind severity rule file line message category <<<"$finding"

  if [[ "$kind" == "hotspot" ]]; then
    label="Hotspot"
    severity_label="review priority $severity"
    category_note=""
    [[ -n "$category" ]] && category_note=" ($category)"
  else
    label="Issue"
    severity_label="$severity"
  fi

  echo ""
  echo "════════════════════════════════════════════════════════"
  echo "  $label $current / $total  [$severity_label]  $rule"
  echo "  File:    $file:$line"
  [[ -n "$category" ]] && echo "  Category: $category"
  echo "  Message: $message"
  echo "════════════════════════════════════════════════════════"

  if [[ "$approve_all" == false ]]; then
    read -rp "  [f]ix / [s]kip / [a]pprove all? " choice </dev/tty
    case "$choice" in
    s | S)
      echo "  Skipping."
      continue
      ;;
    a | A) approve_all=true ;;
    esac
  fi

  if [[ "$REPO" != "montrek" ]]; then
    full_path="$REPO/$file"
  else
    full_path="$file"
  fi

  if [[ "$kind" == "hotspot" ]]; then
    claude --verbose "Review and fix this SonarQube security hotspot in the codebase of $REPO:

[$severity_label] $rule$category_note in $full_path:$line
  $message

Fix the underlying risk in the code. If the code is already safe as written, make
that safety explicit -- constrain the input, narrow the call, or use the safe API
-- instead of only adding a comment or suppressing the rule." </dev/null
  else
    claude --verbose "Fix this SonarQube issue in the codebase of $REPO:

[$severity] $rule in $full_path:$line
  $message" </dev/null
  fi
done

make -C "$PROJECT_ROOT" local-sonarqube-scan
