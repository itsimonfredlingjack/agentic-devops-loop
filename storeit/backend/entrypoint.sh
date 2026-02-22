#!/bin/sh
set -e
alembic upgrade head
exec uvicorn storeit.main:app --host 0.0.0.0 --port 8004
