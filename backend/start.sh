#!/bin/sh
# Container entrypoint for the SOWnia backend.
#
# Works on both Render (which injects $PORT) and any host that doesn't
# ($PORT defaults to 7860). Applies DB migrations before serving so the
# schema is always current; `alembic upgrade head` is idempotent.
set -e

cd /app/backend
alembic upgrade head

cd /app
exec uvicorn backend.api.main:app --host 0.0.0.0 --port "${PORT:-7860}"
