FROM ubuntu:latest

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    texlive-xetex \
    texlive-fonts-recommended \
    ttf-mscorefonts-installer \
    && rm -rf /var/lib/apt/lists/*

# Accept the EULA for the Arial font
RUN echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | debconf-set-selections

# Install Arial font and update font cache
RUN apt-get update && \
    apt-get install -y ttf-mscorefonts-installer && \
    fc-cache -f -v && \
    rm -rf /var/lib/apt/lists/*
