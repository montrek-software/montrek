#!/bin/bash
set -e

. .venv/bin/activate
cd montrek
make sync-local-python-env
python -m celery --app=montrek worker --loglevel=info -Q sequential_queue --concurrency=$1 -n $2@%h
