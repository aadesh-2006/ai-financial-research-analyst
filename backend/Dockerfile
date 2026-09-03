# Production Dockerfile for AI Financial Research Analyst Backend
FROM python:3.12-slim AS runtime

# Prevent python from writing bytecode files and buffer output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install minimal system tools (curl for container health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies without development overhead
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application, database migration files, and startup entrypoint
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY app/ ./app/
COPY scripts/start.sh ./scripts/start.sh
RUN chmod +x ./scripts/start.sh

# Create non-root system user for production security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
    && mkdir -p /app/data_cache && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["./scripts/start.sh"]