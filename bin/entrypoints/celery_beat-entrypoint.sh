#!/bin/bash
set -e

. .venv/bin/activate
cd montrek
make sync-local-python-env
python -m celery --app=montrek beat --loglevel=info
