# base image
FROM python:3.11
# setup environment variable
ENV DOCKERHOME=/montrek

# set work directory
RUN mkdir -p $DOCKERHOME

# where your code lives
WORKDIR $DOCKERHOME

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy whole project to your docker home directory.
COPY . $DOCKERHOME

# Update the package list, install the necessary packages, and clean up in one RUN to keep the image size down
RUN apt-get update && \
    apt-get install -y postgresql-client libjpeg-dev && \
    apt-get install -y build-essential libpq-dev zlib1g-dev libjpeg-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY ./requirements.txt $DOCKERHOME/

# Upgrade pip and install Python dependencies from requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# port where the Django app runs
EXPOSE 8000
