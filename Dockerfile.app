# The app image: montrek-base (./Dockerfile, the system packages) plus the code,
# its locked Python dependencies and the collected static files. Nothing is
# installed or collected when a container starts, so every container started
# from one image runs exactly the same thing.
#
# Code, venv and static files are root-owned and read-only to the app, which
# runs as the base image's appuser; it can write only the runtime paths created
# below and /tmp. The file /montrek/.montrek-image tells the entrypoints that
# they run in such an image rather than on a repo bind mount.
#
#   docker build -f Dockerfile.app --build-arg BASE_IMAGE=<montrek-base ref> .
#
# A requirements.txt in the build context is installed as it is: that is how a
# lock produced elsewhere (CI, a client deployment) gets in. Without one the
# requirements.in files are compiled here, and the result stays in the image
# as /montrek/requirements.txt.
ARG BASE_IMAGE=forgejo.montrek-software.de/montrek-software/montrek-base:latest
FROM ${BASE_IMAGE}

USER root
WORKDIR /montrek
ENV VIRTUAL_ENV=/montrek/.venv \
  PATH=/montrek/.venv/bin:$PATH \
  UV_NO_CACHE=1 \
  PYTHONDONTWRITEBYTECODE=1

# Dependencies first, so a code-only change reuses this layer. The glob makes
# requirements.txt optional.
COPY requirements.in requirements.tx[t] ./
RUN if [ ! -f requirements.txt ]; then \
  uv pip compile requirements.in --output-file requirements.txt; \
  fi \
  && uv venv "$VIRTUAL_ENV" --python "$(command -v python3)" \
  && uv pip sync requirements.txt

COPY bin ./bin
COPY montrek ./montrek

ARG MONTREK_REVISION=unknown
LABEL org.opencontainers.image.source="https://github.com/montrek-software/montrek" \
  org.opencontainers.image.revision="${MONTREK_REVISION}"

# Settings refuse to load without SECRET_KEY and DB_PASSWORD. collectstatic
# needs neither, so placeholders that exist only for this RUN are enough.
RUN cd montrek \
  && SECRET_KEY=collectstatic-only DB_PASSWORD=collectstatic-only \
  python manage.py collectstatic --noinput --verbosity 0 \
  && mkdir -p uploads reporting/.workbench sent_emails \
  && chown appuser:appgroup uploads reporting/.workbench sent_emails \
  && echo "${MONTREK_REVISION}" >/montrek/.montrek-image \
  && chown root:root /montrek

EXPOSE 8000
ENTRYPOINT ["/montrek/bin/entrypoints/montrek-entrypoint.sh"]
USER appuser
