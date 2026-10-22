# Container images

Two images, both built by `.github/workflows/images.yml` and pushed to the
Forgejo package registry (`forgejo.montrek-software.de/montrek-software/...`).

| Image | Built from | Contains | Rebuilt |
| --- | --- | --- | --- |
| `montrek-base` | `Dockerfile` | system packages (TeX, Chromium, pandoc, Node, Postgres client, fonts, gosu) and the entrypoint | when `Dockerfile` or the entrypoint changes, weekly, or by hand |
| `montrek-app` | `Dockerfile.app` | `montrek-base` plus the code, the locked Python dependencies and the collected static files | on every push to `main` and on version tags |

`montrek-app` is tagged `latest` (main), `sha-<commit>` and `<version>` for a
`v<version>` tag; its `org.opencontainers.image.base.name` label names the
base digest it was built and smoke-tested on.

`montrek-container`, which the compose setup on a VM pulls, is the same build
as `montrek-base` and is still built with `make git-build-montrek-container`
until every install runs an app image.

## Two ways to run

**VM install (compose in this repo).** The repo is bind-mounted at `/montrek`.
The containers start as root, install the instance CA, drop to the host user
with `gosu`, sync the venv and, unless `DO_MONTREK_STARTUP_TASKS=0`, migrate and
collect static files on every web start. Unchanged by the app image.

**App image.** The code is baked in and marked by `/montrek/.montrek-image`,
which a bind mount would hide. Code, venv and static files are root-owned and
read-only; the app runs as `appuser` and can write only `montrek/uploads` and
`/tmp`, so the root filesystem can be mounted read-only (with a tmpfs on `/tmp`
and a volume on `uploads`). LaTeX runs compile in a temporary directory that is
removed afterwards; without SMTP, mails go to `/tmp/sent_emails`. On start nothing is installed or collected. Migrations and the
superuser run once per deployment in the release step:

```bash
docker run --rm --env-file .env -e SERVICE=release <montrek-app ref>
```

and web runs with `DO_MONTREK_STARTUP_TASKS=0`. Static files are served by
WhiteNoise, so no nginx is needed in front.

Uploads under `/uploads/` are only served to logged-in users (paths in
`LOGIN_EXEMPT_PATHS` stay public). Django checks the request; with
`MEDIA_X_ACCEL_REDIRECT` set to an internal nginx location (compose sets
`/protected-uploads/`), it answers with an `X-Accel-Redirect` and nginx sends
the file. Without nginx, leave it empty and Django streams the file itself.

All other file access (uploads, upload logs, exports, mailed tables, report
PDFs attached to mail drafts) goes through Django's default storage, which is
the filesystem under `uploads` for now. Upload processors that read the file
by path get the stored file's path, or a temporary copy on a backend without
local paths. A daily Celery Beat task, scheduled by a migration, deletes mailed
tables and report PDFs after seven days.

**Workers.** `SERVICE` (`sequential_worker`, `parallel_worker`, `fast_worker`)
picks the queue and pool. The fast worker is optional (`ENABLE_FAST_WORKER=1`
in compose); the parallel worker runs the fast queue's tasks as well.
`WORKER_CONCURRENCY` sets how many tasks a worker runs at once (parallel 4,
fast 50 per CPU up to 500 by default; sequential always 1).
Set it explicitly where the CPU count is not the container's own, and keep the
fast worker's below what the database allows in connections. Tasks are
acknowledged once they have run, so they must be safe to run twice. On SIGTERM a
prefork worker gives running tasks `CELERY_WORKER_SOFT_SHUTDOWN_TIMEOUT` (8 s) to
finish and puts the rest back in the queue; the gevent fast worker keeps the
warm shutdown, and a task it is killed in comes back after
`CELERY_VISIBILITY_TIMEOUT` (10 h). Keep the platform's stop timeout above 8 s.

An instance CA (`MONTREK_CA_CERT`, default `/montrek/nginx/certs/fullchain.crt`)
cannot be installed system-wide without root; the entrypoint appends it to a
private bundle under `/tmp` and points `REQUESTS_CA_BUNDLE` and `SSL_CERT_FILE`
at it. Started as root, an app image installs it system-wide and drops to
`appuser` instead.

## Building locally

```bash
docker build -f Dockerfile.app --build-arg BASE_IMAGE=<montrek-base ref> -t montrek-app:dev .
```

A `requirements.txt` in the repo root (the one `make sync-local-python-env`
writes) is installed as it is; without one, `requirements.in` is compiled
during the build. The context is limited by `Dockerfile.app.dockerignore`
(Docker reads it instead of `.dockerignore` for that Dockerfile), which keeps
runtime data and any `montrek/mt_*` extension checked out locally out of a core
image.

## Client images

A client image is built with the same `Dockerfile.app`, from `montrek-base`
rather than on top of `montrek-app`, so core and extension dependencies are
resolved into one lock. Its pipeline assembles the build context: core at the
pinned version, each extension under `montrek/<extension>`, the client's
committed `requirements.txt` in the root, and a `Dockerfile.app.dockerignore`
without the `montrek/mt_*` line.
