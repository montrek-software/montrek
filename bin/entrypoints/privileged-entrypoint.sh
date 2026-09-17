#!/bin/bash
set -e

# Runs as root, before montrek-entrypoint.sh drops to PUID:PGID. Everything
# here is work the unprivileged app user cannot do for itself.
#
# PUID/PGID are resolved independently rather than relying on the caller, so
# this behaves the same whether it is invoked before or after the caller
# resolves them. montrek-entrypoint.sh is the one script baked into the image,
# so an older image calls this in the other order.
: "${PUID:=$(stat -c %u /montrek)}"
: "${PGID:=$(stat -c %g /montrek)}"

if [[ -f /montrek/nginx/certs/fullchain.crt ]]; then
  echo "Installing instance-specific certificate system-wide..."
  cp /montrek/nginx/certs/fullchain.crt /usr/local/share/ca-certificates/montrek_root_ca.crt
  update-ca-certificates
fi

# Paths the app writes at startup: collectstatic into the static volume, uv
# into the venv and requirements.txt, uploads at runtime. While the privilege
# drop was broken every service ran as root and left these root-owned, so on
# the first correctly-dropped boot they are unwritable. Repaired only when the
# ownership is actually wrong, so a healthy boot does no work.
# Fixes only the entries whose ownership is actually wrong. Checking just the
# top-level directory is not enough: .venv is 1000-owned but has root-owned
# children (.lock, share/, include/) from the root-era boots, so a top-level
# check would skip exactly the files that break `uv`.
repair_owner() {
  local path="$1"
  [[ -e "$path" ]] || return 0

  # `|| true` is load-bearing. `-quit` makes find exit 0 as soon as it finds a
  # wrongly-owned entry, but when everything is already correct it walks the
  # whole tree -- and exits 1 if any directory is unreadable. This runs as root
  # with cap_drop: ALL, so root has no CAP_DAC_OVERRIDE and cannot enter a
  # 0700 directory it does not own. Without `|| true`, `set -e` then killed the
  # entrypoint inside the command substitution, with stderr suppressed: the boot
  # simply stopped after the CA install, printing nothing, and the container
  # restart-looped. A healthy boot is exactly the case that triggered it.
  local wrong find_errors
  find_errors="$(mktemp)"
  wrong="$(find "$path" \( -not -user "$PUID" -o -not -group "$PGID" \) -print -quit 2>"$find_errors" || true)"
  if [[ -s "$find_errors" ]]; then
    echo "WARN: could not fully scan $path for ownership:" >&2
    sed 's/^/  /' "$find_errors" >&2
  fi
  rm -f "$find_errors"
  [[ -z "$wrong" ]] && return 0

  echo "Repairing ownership under $path (-> ${PUID}:${PGID})..."
  # Non-fatal: a crash loop here is worse than the specific error the app will
  # raise next if this genuinely cannot be fixed.
  find "$path" \( -not -user "$PUID" -o -not -group "$PGID" \) \
    -exec chown "${PUID}:${PGID}" {} + 2>/dev/null ||
    echo "WARN: could not fix ownership under $path" >&2
}

if [[ -n "${PUID:-}" && -n "${PGID:-}" && "$PUID" != "0" ]]; then
  repair_owner /montrek/static
  repair_owner /montrek/.venv
  repair_owner /montrek/requirements.txt
  repair_owner /montrek/montrek/uploads
fi
