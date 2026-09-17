# Secrets and deployment hardening

How configuration reaches the application, what the current setup protects
against, and what it does not.

## Where configuration lives

| File           | Contents                                       | Reaches a container?         |
| -------------- | ---------------------------------------------- | ---------------------------- |
| `.env`         | Runtime config: DB name, hosts, mail, Celery   | Yes, via `env_file:`         |
| `secrets/*`    | One secret per file: passwords, `SECRET_KEY`   | Only where declared, as a file |
| `.env.build`   | Registry token (`GIT_PAT`), `SONARCUBE_TOKEN`  | No                           |

Anything not needed at runtime belongs in `.env.build`. A registry write token
in `.env` turns an application compromise into a supply-chain compromise,
because every app container can read it.

### Resolution order

Every value resolves the same way in Django (`montrek/configuration.py`) and in
the shell scripts (`montrek_load_secrets` in `bin/lib/load-env.sh`):

```
environment  >  NAME_FILE  >  /run/secrets/name  >  .env  >  built-in default
```

The environment winning means a local override or a CI variable still takes
effect against an install that has secret files mounted. A missing `.env` is not
an error at any layer: a container is configured through `env_file:` and
`secrets:` and deliberately has no readable one.

An **empty** secret file counts as unset and falls through to the next source.
Compose refuses to start when a declared `secrets: file:` source is missing, so
`make secrets-init` creates a file for every secret in the overlay and leaves
the ones this install does not use empty.

## What the containers can and cannot see

The repo is bind-mounted at `/montrek`, which would put the plaintext `.env`,
the build-time `.env.build` and the whole of `secrets/` inside the containers
most likely to be compromised. All three are therefore shadowed:

```yaml
volumes:
  - .:/montrek
  - /dev/null:/montrek/.env:ro
  - /dev/null:/montrek/.env.build:ro
  - type: tmpfs
    target: /montrek/secrets
```

`env_file:` has already injected the runtime values and each service's own
secrets are mounted at `/run/secrets`, so nothing breaks. `/dev/null` only works
for a file, hence the empty tmpfs for the directory. Scoping secrets per service
would be pointless if the repo mount handed every container the whole `secrets/`
directory anyway.

## Privilege model

Each service built from the montrek image starts as root so
`privileged-entrypoint.sh` can install the instance CA, then
`montrek-entrypoint.sh` drops to `PUID:PGID` via `gosu` before exec'ing
gunicorn or celery. `PUID`/`PGID` come from the host user (`make docker-up`
exports `USER_ID`/`GROUP_ID`), because that uid has to own the bind-mounted
repo.

The entrypoint refuses to run the app as root unless `MONTREK_ALLOW_ROOT=1` is
set. A silent fallback to root is how the earlier `PIUD`/`PGUD` typo went
unnoticed for as long as it did.

Capabilities are `cap_drop: ALL` plus only `SETUID`, `SETGID` (for `gosu`) and
`CHOWN` (to give the dropped-to uid a writable `HOME`), with
`no-new-privileges:true`. After the drop the process has no effective
capabilities at all.

The dropped-to uid has no `/etc/passwd` entry and so no home directory. The
entrypoint points `HOME`, `XDG_CACHE_HOME`, `XDG_CONFIG_HOME` and
`MPLCONFIGDIR` at a writable path, re-applying them past `gosu` (which rewrites
`HOME` from the passwd entry). Without this, matplotlib, uv, fontconfig,
chromium and texlive all try to cache under `/`.

## Network surface

`nginx` is the only service with a published port. The database is bound to
`127.0.0.1` so host tooling still reaches it while the network does not.
`web` and `flower` are `expose`d only and reachable through nginx.

Publishing the gunicorn port is specifically unsafe: it serves the app over
plaintext HTTP next to the TLS vhost, and because `SECURE_PROXY_SSL_HEADER`
trusts `X-Forwarded-Proto`, a client that can reach gunicorn directly can
assert its own value and defeat every HTTPS-related check in `settings.py`.

## What `make secrets-encrypt` does and does not buy

It encrypts `.env` at rest with `ansible-vault`. That covers exactly one
threat: someone reading the file while the whole stack is stopped.

It does not cover:

- **Runtime.** `bin/secrets/secure-wrapper.sh` decrypts the file for the
  duration of a wrapped command, and the stack keeps running long after that
  command exits. In normal operation the file is plaintext.
- **Docker access.** Every `env_file:` value is materialized into the container
  config and readable via `docker inspect`. Anyone in the `docker` group --
  which is effectively root -- reads the secrets without touching the file.
  This is the hard ceiling on any file-encryption scheme on a single host.
- **Crashes.** Re-encryption runs from a shell `trap ... EXIT`, which does not
  fire on `SIGKILL`, OOM or power loss. The file is then left plaintext with
  the `.env.encrypted` marker already removed.
- **The password itself.** The wrapper passes the vault password as an argv to
  `encrypt.sh`, where any local user can read it out of `ps`.

Treat it as tidiness, not as a control, and do not let it justify weaker
handling elsewhere. The section below removes the second and third of those
problems for the values that matter; it does not replace the encryption, which
is what SOPS is for.

## Compose file-based secrets

`make secrets-init` moves each secret out of `.env` into its own file under
`secrets/`, and `bin/docker/run.sh` then layers `secrets.yml` on top of the
compose files. Each secret becomes a read-only bind mount at
`/run/secrets/<name>` in only the services that declare it.

What that buys, over `env_file:`:

- The container config records a **path**, not a value, so `docker inspect` and
  `docker compose config` no longer hand out the secrets.
- A secret is no longer inherited by every child process of the entrypoint.
- Each secret is scoped: `admin_password` reaches `web` and nothing else,
  `flower_password` reaches `flower` and nothing else.

A secret file is named after the variable it replaces, lowercased --
`secrets/db_password` provides `DB_PASSWORD` -- so nothing needs per-variable
wiring and nothing can drift. The list lives in `bin/lib/secrets.sh` and must
match the `secrets:` block in `secrets.yml`; `init-secrets.sh` checks that on
every run.

The third-party images cannot follow that rule, so they are wired explicitly
through the `*_FILE` convention they already support: `POSTGRES_PASSWORD_FILE`
and `MYSQL_*_PASSWORD_FILE` for `db`, `KC_DB_PASSWORD_FILE` and friends for
`keycloak` (read by `keycloak/bin/init-realm.sh`, which is the entrypoint).
Flower has no `*_FILE` support at all, so its basic-auth credential is assembled
in the shell that already wraps its command -- into that process's environment
rather than into argv, where `ps` inside the container would show it.

### Migrating

```bash
make secrets-init      # run as the user that runs `make docker-up`
make docker-restart
```

It is idempotent and reversible: a value left in `.env` still wins, so putting
one back is enough to undo the move for that secret. `run.sh` adds the overlay
only once every declared file exists, so an install that has not migrated keeps
running exactly as before.

### File permissions

Compose **ignores** the `uid`, `gid` and `mode` fields of a file secret outside
swarm -- it warns about it and bind-mounts the host file as it is. So the host
file's ownership is what the container sees, which is why `init-secrets.sh` must
run as the user the app containers drop to, and why the secrets read by postgres
(uid 999), flower and keycloak (uid 1000) are `0644` rather than `0600`.

That costs less than it looks like. The montrek containers run as the host user,
who *owns* every one of these files, so `0600` would not stop a compromised
montrek container from reading the ones mounted into it either. The host-side
gate is the `0700` `secrets/` directory.

### What it still does not do

It does not encrypt anything at rest, and it does not hide anything from root or
from the `docker` group. For encryption at rest, see below.

## Stronger options, in increasing order of effort

1. **SOPS + age** (or `git-crypt`). Encrypts values rather than the whole file,
   so config stays diffable and reviewable in git, with keys in `age` or a KMS
   and decryption at deploy time. This is the proper replacement for
   `make secrets-encrypt`: no argv password, no marker-file state, no plaintext
   window tied to a trap handler. For many customer installs: one encrypted
   file per install, per-install keys.
2. **A secret manager** (Vault/OpenBao, Infisical, or AWS/GCP/Azure native).
   Central rotation, an audit log, short-lived dynamic database credentials and
   per-service policy. Needs an HA service and a trust bootstrap on every host.
   On GCP, Secret Manager plus workload identity is the low-friction version,
   and Cloud SQL IAM auth removes `DB_PASSWORD` entirely.

## Operational notes

- Set `KEYCLOAK_ADMIN_PASSWORD` and `FLOWER_PASSWORD`. Both fall back to
  `ADMIN_PASSWORD` for compatibility, which makes one credential the Django
  superuser, the Keycloak realm admin and the Flower UI at once.
- `DEBUG=1` with a non-local `DEPLOY_HOST` raises `ImproperlyConfigured` at
  startup rather than serving error pages full of settings and SQL. Override
  with `MONTREK_ALLOW_DEBUG=1` if you really mean it.
- After `make secrets-init`, check what is left in the container config:
  `docker compose -f docker-compose.yml -f secrets.yml config | grep -i -e password -e secret_key`
  should show only `/run/secrets/...` paths.
- An extension app can add its own secret: put the value in
  `secrets/<lowercased variable>`, add it to `MONTREK_SECRET_NAMES` in
  `bin/lib/secrets.sh` and to both blocks in `secrets.yml`. No Python change is
  needed -- `config("AZURE_CLIENT_SECRET")` finds
  `/run/secrets/azure_client_secret` on its own.
- Changes to `bin/entrypoints/montrek-entrypoint.sh` need
  `make git-build-montrek-container`: that one file is `COPY`'d into the image,
  unlike the scripts it calls, which come from the bind mount.
