#!/bin/bash

make docker-down
make git-update-repositories
make docker-up
make docker-cleanup
