#!/bin/bash

TARGET_REPOSITORY=$1

echo "Cloning $TARGET_REPOSITORY..."
cd montrek

git clone git@github.com:montrek-software/$TARGET_REPOSITORY.git
