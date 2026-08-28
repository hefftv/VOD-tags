#!/usr/bin/env sh
set -e

mkdir -p "$(dirname "${DJANGO_DB_PATH:-/app/webapp/data/db.sqlite3}")"
python manage.py migrate --noinput
exec python manage.py runserver 0.0.0.0:8000
