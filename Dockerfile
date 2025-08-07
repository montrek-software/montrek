# Use an Ubuntu base image
FROM ubuntu:24.04

# setup environment variable
ENV DOCKERHOME=/montrek

# set work directory
RUN mkdir -p $DOCKERHOME

# where your code lives
WORKDIR $DOCKERHOME

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive


# Install system dependencies
RUN apt-get update && apt-get install -y \
  python3.12 \
  make \
  curl \
  texlive-xetex \
  texlive-fonts-recommended \
  fontconfig \
  wget \
  software-properties-common \
  pkg-config \
  libmysqlclient-dev \
  libpq-dev gcc \
  graphviz \
  libgraphviz-dev \
  && apt-get clean

# Enable the multiverse repository
RUN add-apt-repository multiverse && apt-get update

# Accept the EULA and install Microsoft core fonts
RUN echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections \
  && apt-get install -y ttf-mscorefonts-installer \
  && fc-cache -f -v

# Install postgres utils
RUN apt-get update && \
  apt-get install -y postgresql-client && \
  rm -rf /var/lib/apt/lists/*
# Install uv from prebuilt binaries
RUN curl -Ls https://astral.sh/uv/install.sh | bash && \
  cp /root/.local/bin/uv /usr/local/bin/uv
RUN ln -s /usr/bin/python3.12 /usr/bin/python && \
  ln -s /usr/bin/pip3 /usr/bin/pip
# copy whole project to your docker home directory.
COPY . $DOCKERHOME

# port where the Django app runs
EXPOSE 8000


# Copy certs
RUN apt-get install -y --no-install-recommends ca-certificates

COPY ./nginx/certs/fullchain.crt /usr/local/share/ca-certificates/montrek_root_ca.crt
RUN update-ca-certificates
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
# Clean up
RUN rm -rf /var/lib/apt/lists/*
