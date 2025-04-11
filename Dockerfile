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
  python3-pip \
  python3-venv \
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
# Create a virtual environment
RUN python3 -m venv /venv

# Activate the virtual environment and upgrade pip
RUN /venv/bin/pip install --upgrade pip
# copy whole project to your docker home directory.
COPY . $DOCKERHOME

# Install Python dependencies within the virtual environment
RUN /venv/bin/pip install -r requirements.txt

# Find and install dependencies from all requirements.txt files in subdirectories
RUN find . -type f -name "requirements.txt" ! -path "./requirements.txt" -exec /venv/bin/pip install -r {} \;

# Install postgres utils
RUN apt-get update && \
  apt-get install -y postgresql-client && \
  rm -rf /var/lib/apt/lists/*

# Set the entrypoint to use the virtual environment's Python
ENV PATH="/venv/bin:$PATH"

# port where the Django app runs
EXPOSE 8000

# Clean up
RUN rm -rf /var/lib/apt/lists/*
