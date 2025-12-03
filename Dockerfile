FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
# Create a user and group (with no password, home dir, and no shell access)
RUN addgroup --system appgroup && \
  adduser --system --ingroup appgroup --home /home/appuser appuser
# setup environment variable
ENV DOCKERHOME=/montrek
# set work directory
RUN mkdir -p $DOCKERHOME
# where your code lives
WORKDIR $DOCKERHOME
# Install required system dependencies
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  build-essential \
  ca-certificates \
  chromium \
  curl \
  fontconfig \
  git \
  gnupg \
  gosu \
  libmariadb-dev \
  libpq-dev \
  lsb-release \
  pkg-config \
  python3-dev \
  texlive-fonts-recommended \
  texlive-xetex \
  unzip \
  && mkdir -p /etc/apt/keyrings \
  && curl --fail --silent --show-error \
  --proto '=https' --tlsv1.2 \
  https://www.postgresql.org/media/keys/ACCC4CF8.asc \
  | gpg --dearmor -o /etc/apt/keyrings/postgresql.gpg \
  && echo "deb [signed-by=/etc/apt/keyrings/postgresql.gpg] https://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" \
  > /etc/apt/sources.list.d/pgdg.list \
  && echo "deb https://deb.debian.org/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list \
  && echo "deb https://deb.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list \
  && echo "deb https://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list \
  && apt-get update \
  && echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections \
  && apt-get install -y --no-install-recommends \
  ttf-mscorefonts-installer \
  postgresql-client-16 \
  && chown -R appuser:appgroup ${DOCKERHOME} \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
# port where the Django app runs
EXPOSE 8000
# Copy entrypoint
COPY bin/entrypoints/montrek-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# Run as root initially
ENTRYPOINT ["/entrypoint.sh"]
# Switch to the non-root user
USER appuser
