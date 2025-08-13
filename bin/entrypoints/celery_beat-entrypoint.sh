#!/bin/bash
set -e

. .venv/bin/activate
make sync-local-python-env
cd montrek
python -m celery --app=montrek beat --loglevel=info
