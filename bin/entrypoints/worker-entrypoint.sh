#!/bin/bash
set -e

. .venv/bin/activate
cd montrek
python -m celery --app=montrek worker --loglevel=info -Q $QUEUE --concurrency=$1 -n $SERVICE@%h --pool=$POOL
