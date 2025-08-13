#!/bin/bash
set -e

. .venv/bin/activate
cd montrek
python -m celery --app=montrek beat --loglevel=info
