#!/usr/bin/env bash
# Postgres backup and restore, shared by bin/local/db.sh and
# bin/local/keycloak-db.sh.
#
# Backups are written in pg_dump's custom format by default: a compressed
# binary archive that pg_restore reads. Plain SQL stays available behind
# --plain for the transition away from the old text dumps, and a restore
# accepts either, whatever it was asked for, because the format is detected
# from the file itself.
#
#   <script> backup            # custom format -> <prefix>_<date>.dump
#   <script> backup --plain    # plain SQL     -> <prefix>_<date>.sql
#   <script> restore           # newest backup for the date, either format
#   <script> restore --plain   # only consider plain-SQL backups
#   <script> restore --binary  # only consider custom-format backups
#
# DB_BACKUP_FORMAT=plain in the environment flips the backup default, so a
# deployment that is not ready for binary dumps does not have to change the
# call site.
#
# The caller sets the MONTREK_DB_* configuration below, then calls
# montrek_db_parse_args "$@" and montrek_db_dispatch. Parsing is a separate
# step so a script can print its own configuration summary in between, and so
# an unusable argument is rejected before anything touches the database.
#
# Source it, don't execute it:  . bin/lib/db-backup.sh
#
#   MONTREK_DB_LABEL     what the database is called in messages
#   MONTREK_DB_PREFIX    backup filename prefix, which also scopes the pruning
#   MONTREK_DB_HOST      }
#   MONTREK_DB_PORT      }
#   MONTREK_DB_NAME      } connection details
#   MONTREK_DB_USER      }
#   MONTREK_DB_PASSWORD  }

# Set default for DB_BACKUP_KEEP_DAYS if not provided
: "${DB_BACKUP_KEEP_DAYS:=30}"
# Set default backup format if not provided: custom is pg_dump's compressed
# binary archive, plain is the legacy SQL text dump.
: "${DB_BACKUP_FORMAT:=custom}"

MONTREK_DB_BACKUP_FOLDER="${MONTREK_DB_BACKUP_FOLDER:-db_backups}"
# Both extensions are pruned by the retention rules and both are offered to a
# restore, so the plain dumps written before the switch stay usable.
MONTREK_DB_EXTENSIONS=(dump sql)

montrek_db_usage() {
  echo "Usage: $(basename "$0") {backup|restore} [--plain|--binary]" >&2
}

# Fills in MONTREK_DB_COMMAND, MONTREK_DB_FORMAT (what a backup writes) and
# MONTREK_DB_RESTORE_EXTENSIONS (what a restore is willing to read).
montrek_db_parse_args() {
  MONTREK_DB_COMMAND="$1"
  shift 2>/dev/null

  MONTREK_DB_FORMAT="$DB_BACKUP_FORMAT"
  MONTREK_DB_RESTORE_EXTENSIONS=("${MONTREK_DB_EXTENSIONS[@]}")

  while (($#)); do
    case "$1" in
    --plain | --format=plain)
      MONTREK_DB_FORMAT=plain
      MONTREK_DB_RESTORE_EXTENSIONS=(sql)
      ;;
    --binary | --custom | --format=custom)
      MONTREK_DB_FORMAT=custom
      MONTREK_DB_RESTORE_EXTENSIONS=(dump)
      ;;
    "") ;; # `make` hands through an empty argument when FORMAT is unset
    *)
      echo "Unknown option: $1" >&2
      montrek_db_usage
      return 1
      ;;
    esac
    shift
  done

  if [[ "$MONTREK_DB_FORMAT" != "custom" && "$MONTREK_DB_FORMAT" != "plain" ]]; then
    echo "Unknown backup format: $MONTREK_DB_FORMAT (expected 'custom' or 'plain')" >&2
    return 1
  fi
}

# psql and pg_dump are given the password through ~/.pgpass rather than
# PGPASSWORD, which would be readable in the process environment. The database
# field is a wildcard because the restore path connects to `postgres` to drop
# and recreate the database.
montrek_db_write_pgpass() {
  echo "$MONTREK_DB_HOST:$MONTREK_DB_PORT:*:$MONTREK_DB_USER:$MONTREK_DB_PASSWORD" >~/.pgpass
  chmod 600 ~/.pgpass
}

montrek_db_psql() {
  psql -U "$MONTREK_DB_USER" -h "$MONTREK_DB_HOST" -p "$MONTREK_DB_PORT" "$@"
}

# Custom-format archives start with the magic string PGDMP; anything else is
# treated as plain SQL. Read from the file rather than trusting the extension,
# so a dump that was renamed still restores correctly.
montrek_db_detect_format() {
  if [[ "$(head -c 5 -- "$1" 2>/dev/null)" == "PGDMP" ]]; then
    echo custom
  else
    echo plain
  fi
}

# Delete backups older than a year, and backups older than
# DB_BACKUP_KEEP_DAYS unless they are the last one of their month. Scoped to
# the caller's prefix so the two databases sharing this folder do not prune
# each other's dumps.
montrek_db_prune() {
  local extension file base file_date year month day last_day

  for extension in "${MONTREK_DB_EXTENSIONS[@]}"; do
    find "$MONTREK_DB_BACKUP_FOLDER" -type f \
      -name "${MONTREK_DB_PREFIX}_*.$extension" -mtime +365 -exec rm {} \;

    find "$MONTREK_DB_BACKUP_FOLDER" -type f \
      -name "${MONTREK_DB_PREFIX}_*.$extension" -mtime "+$DB_BACKUP_KEEP_DAYS" |
      while IFS= read -r file; do
        # <prefix>_YYYY-MM-DD_HH-MM-SS.<extension>
        base=$(basename "$file")
        file_date="${base#"${MONTREK_DB_PREFIX}_"}"
        file_date="${file_date%%_*}"
        [[ "$file_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || continue

        year="${file_date%%-*}"
        month="${file_date:5:2}"
        day="${file_date##*-}"

        last_day=$(date -d "$year-$month-01 +1 month -1 day" +"%d")

        if [ "$day" != "$last_day" ]; then
          echo "Removing file: $file (Not the last day of the month)"
          rm "$file"
        fi
      done
  done
}

montrek_db_backup() {
  local date_stamp backup_file
  local -a dump_options

  date_stamp=$(date +"%Y-%m-%d_%H-%M-%S")

  if [[ "$MONTREK_DB_FORMAT" == "custom" ]]; then
    # The custom format is a compressed binary archive; the highest
    # compression level trades CPU for the smallest file, which is the right
    # side of that trade for a nightly cron job.
    backup_file="$MONTREK_DB_BACKUP_FOLDER/${MONTREK_DB_PREFIX}_$date_stamp.dump"
    dump_options=(--format=custom --compress=9)
  else
    backup_file="$MONTREK_DB_BACKUP_FOLDER/${MONTREK_DB_PREFIX}_$date_stamp.sql"
    dump_options=(--format=plain)
  fi

  echo "Backup format: $MONTREK_DB_FORMAT"

  # Ensure the backup folder exists
  mkdir -p "$MONTREK_DB_BACKUP_FOLDER"

  montrek_db_write_pgpass

  # -f rather than a shell redirect, so a failed dump does not leave a
  # zero-length file behind that looks like a backup.
  if pg_dump -U "$MONTREK_DB_USER" -h "$MONTREK_DB_HOST" -d "$MONTREK_DB_NAME" \
    -p "$MONTREK_DB_PORT" "${dump_options[@]}" -f "$backup_file"; then
    echo "Backup successful! File: $backup_file"
  else
    echo "Backup failed!"
    rm -f "$backup_file"
    return 1
  fi

  montrek_db_prune
}

# Terminate whatever is still connected, after showing the user what it is.
# Returns non-zero when the user declines, which aborts the restore.
montrek_db_clear_connections() {
  local active_count confirm

  echo "Checking for active connections to $MONTREK_DB_NAME..."

  active_count=$(montrek_db_psql -d postgres -t -c "
  SELECT count(*) FROM pg_stat_activity WHERE datname = '${MONTREK_DB_NAME}' AND pid <> pg_backend_pid();
  " | xargs)

  if [ "$active_count" -gt 0 ]; then
    echo ""
    echo "⚠️  There are currently $active_count active connection(s) to $MONTREK_DB_NAME:"
    echo ""

    montrek_db_psql -d postgres -c "
    SELECT pid, usename AS user, application_name, client_addr, state, query
    FROM pg_stat_activity
    WHERE datname = '${MONTREK_DB_NAME}' AND pid <> pg_backend_pid();
    "

    echo ""
    read -r -p "Do you want to terminate all these connections? [y/N]: " confirm

    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
      return 1
    fi

    echo "Terminating all active connections..."
    montrek_db_psql -d postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '${MONTREK_DB_NAME}' AND pid <> pg_backend_pid();
    "
  else
    echo "No active connections found. Proceeding..."
  fi
}

montrek_db_restore() {
  local restore_date backup_file restore_format confirm extension status
  local -a find_args

  read -r -p "Enter the date of the $MONTREK_DB_LABEL backup to restore (format: YYYY-MM-DD): " restore_date

  if ! [[ $restore_date =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "Invalid date format. Please use YYYY-MM-DD."
    return 0
  fi

  # Collect every candidate for that date across the accepted formats and pick
  # the most recent one by modification time.
  find_args=()
  for extension in "${MONTREK_DB_RESTORE_EXTENSIONS[@]}"; do
    ((${#find_args[@]})) && find_args+=(-o)
    find_args+=(-name "${MONTREK_DB_PREFIX}_${restore_date}_*.$extension")
  done

  # Sorted here rather than by `xargs ls -t`, which re-sorts within each batch
  # once the list outgrows one command line and would then not return the
  # newest file overall. The second key breaks a tie between a .dump and a .sql
  # written in the same second in favour of the binary one.
  backup_file=$(find "$MONTREK_DB_BACKUP_FOLDER" -type f \( "${find_args[@]}" \) \
    -printf '%T@\t%p\n' | sort -k1,1nr -k2,2 | head -n 1 | cut -f2-)

  if [ -z "$backup_file" ]; then
    echo "No $MONTREK_DB_LABEL backup file found for date: $restore_date"
    return 0
  fi

  restore_format=$(montrek_db_detect_format "$backup_file")
  echo "Found backup: $backup_file ($restore_format format)"

  read -r -p "Are you sure you want to restore the $MONTREK_DB_LABEL from this backup? (y/n): " confirm

  if [[ $confirm != "y" ]]; then
    echo "Restore operation cancelled."
    return 1
  fi

  montrek_db_write_pgpass

  if ! montrek_db_clear_connections; then
    echo "Aborting. Restore of the $MONTREK_DB_LABEL cancelled."
    return 1
  fi

  echo ""
  echo "Dropping and recreating the $MONTREK_DB_LABEL..."

  montrek_db_psql -d postgres -c "DROP DATABASE IF EXISTS $MONTREK_DB_NAME;"
  montrek_db_psql -d postgres -c "CREATE DATABASE $MONTREK_DB_NAME;"

  echo "Restoring the $MONTREK_DB_LABEL from backup..."

  status=0
  if [[ "$restore_format" == "custom" ]]; then
    # The database was just recreated by $MONTREK_DB_USER, so ownership and
    # grants from the source cluster are dropped rather than replayed against
    # roles that may not exist here. --exit-on-error because pg_restore
    # otherwise counts errors, reports them and still exits 0, which would
    # report a half-restored database as a success.
    pg_restore -U "$MONTREK_DB_USER" -h "$MONTREK_DB_HOST" -d "$MONTREK_DB_NAME" \
      -p "$MONTREK_DB_PORT" --no-owner --no-privileges --exit-on-error \
      "$backup_file" || status=$?
  else
    # Left as tolerant as it has always been: a legacy dump that produces
    # ignorable errors must still restore during the transition.
    montrek_db_psql -d "$MONTREK_DB_NAME" <"$backup_file" || status=$?
  fi

  if ((status == 0)); then
    echo "✅ Restored the $MONTREK_DB_LABEL successfully from backup: $backup_file"
  else
    echo "❌ Restore of the $MONTREK_DB_LABEL failed!"
    return 1
  fi
}

montrek_db_dispatch() {
  case "$MONTREK_DB_COMMAND" in
  backup) montrek_db_backup ;;
  restore) montrek_db_restore ;;
  "")
    montrek_db_usage
    return 1
    ;;
  *)
    echo "Unknown command: $MONTREK_DB_COMMAND" >&2
    montrek_db_usage
    return 1
    ;;
  esac
}
