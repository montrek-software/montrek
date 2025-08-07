FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# setup environment variable
ENV DOCKERHOME=/montrek

# set work directory
RUN mkdir -p $DOCKERHOME

# where your code lives

WORKDIR $DOCKERHOME

# Install required system dependencies
RUN apt-get update && \
  apt-get install -y \
  texlive-xetex \
  texlive-fonts-recommended \
  fontconfig \
  graphviz \
  libgraphviz-dev \
  libmariadb-dev \
  libpq-dev \
  unzip \
  make \
  git \
  curl && \
  apt-get clean && rm -rf /var/lib/apt/lists/*
# Add contrib/non-free to apt sources (Debian Bookworm slim)
RUN echo "deb http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
  echo "deb http://deb.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
  echo "deb http://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
  apt-get update && \
  echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections && \
  apt-get install -y ttf-mscorefonts-installer && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy certs
RUN apt-get install -y --no-install-recommends ca-certificates
# port where the Django app runs
EXPOSE 8000
# Clean up
RUN rm -rf /var/lib/apt/lists/*
