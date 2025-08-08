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
  ca-certificates\
  curl \
  fontconfig \
  git \
  gosu \
  graphviz \
  libgraphviz-dev \
  libmariadb-dev \
  libpq-dev \
  make \
  texlive-fonts-recommended \
  texlive-xetex \
  unzip && \
  # Add contrib/non-free to apt sources (Debian Bookworm slim)
  echo "deb https://deb.debian.org/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
  echo "deb https://deb.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
  echo "deb https://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
  apt-get update && \
  echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections && \
  apt-get install -y --no-install-recommends \
  ttf-mscorefonts-installer &&\
  # Copy certs
  apt-get clean && rm -rf /var/lib/apt/lists/* &&\
  # Set permissions if needed
  chown -R appuser:appgroup ${DOCKERHOME}
# port where the Django app runs
EXPOSE 8000
# Copy entrypoint
COPY bin/entrypoints/montrek-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run as root initially
ENTRYPOINT ["/entrypoint.sh"]
# Switch to the non-root user
# TODO: Handle Non Root user
# USER appuser
