# Secrets and deployment hardening

How configuration reaches the application, what the current setup protects
against, and what it does not.

## Where configuration lives

| File           | Contents                                             | Reaches a container? |
| -------------- | ---------------------------------------------------- | -------------------- |
| `.env`         | Runtime config: `SECRET_KEY`, DB, mail, Celery       | Yes, via `env_file:` |
| `.env.build`   | Registry token (`GIT_PAT`), `SONARCUBE_TOKEN`        | No                   |

Both are loaded by `bin/lib/load-env.sh`, which fills in only the variables
that are not already set. The environment always wins over the file. This is
the same precedence `python-decouple` uses in `settings.py`, so the shell
scripts and Django agree, and it means a container or a CI job can be
configured entirely through the environment with no file present.

Anything not needed at runtime belongs in `.env.build`. A registry write token
in `.env` turns an application compromise into a supply-chain compromise,
because every app container can read it.

## What the containers can and cannot see

The repo is bind-mounted at `/montrek`, which would put the plaintext `.env`
inside the containers most likely to be compromised. It is therefore shadowed:

```yaml
volumes:
  - .:/montrek
  - /dev/null:/montrek/.env:ro
```

`env_file:` has already injected the values, so nothing breaks, and
`/montrek/.env` reads as empty from inside the container.

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
handling elsewhere.

## Stronger options, in increasing order of effort

1. **Compose file-based secrets.** Top-level `secrets:` with `file:`, mounted
   read-only at `/run/secrets/<name>`, declared per service. Keeps values out
   of `docker inspect` and out of child process environments, and scopes each
   secret to the services that need it. Needs a `*_FILE` convention in
   `settings.py`. Does not encrypt anything at rest.
2. **SOPS + age** (or `git-crypt`). Encrypts values rather than the whole file,
   so config stays diffable and reviewable in git, with keys in `age` or a KMS
   and decryption at deploy time. This is the proper replacement for
   `make secrets-encrypt`: no argv password, no marker-file state, no plaintext
   window tied to a trap handler. For many customer installs: one encrypted
   file per install, per-install keys.
3. **A secret manager** (Vault/OpenBao, Infisical, or AWS/GCP/Azure native).
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
- Changes to `bin/entrypoints/montrek-entrypoint.sh` need
  `make git-build-montrek-container`: that one file is `COPY`'d into the image,
  unlike the scripts it calls, which come from the bind mount.
