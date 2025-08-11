FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

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
  curl \
  fontconfig \
  git \
  gosu \
  graphviz \
  libgraphviz-dev \
  libmariadb-dev \
  libpq-dev \
  pkg-config \
  python3-dev \
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
  ttf-mscorefonts-installer && \
  # Copy certs
  apt-get clean && rm -rf /var/lib/apt/lists/*
# port where the Django app runs
EXPOSE 8000
# Copy entrypoint
COPY bin/entrypoints/montrek-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run as root initially
ENTRYPOINT ["/entrypoint.sh"]
