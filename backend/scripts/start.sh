#!/usr/bin/env bash
set -e

echo "==> Applying database migrations (alembic upgrade head)..."
alembic upgrade head

echo "==> Starting FastAPI ASGI server (uvicorn)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2}