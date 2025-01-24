#!/bin/bash

docker compose exec web python montrek/manage.py collectstatic
