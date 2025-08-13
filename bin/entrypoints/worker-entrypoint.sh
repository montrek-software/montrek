#!/bin/bash
set -e

. .venv/bin/activate
make sync-local-python-env
cd montrek
python -m celery --app=montrek worker --loglevel=info -Q sequential_queue --concurrency=$1 -n $2@%h
