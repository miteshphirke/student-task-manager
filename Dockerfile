# ---- Student Task Manager: Docker image ----
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout (cleaner Docker logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better Docker layer caching)
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ .

# SQLite database will live in this folder; mount it as a volume in docker-compose
# so data survives container restarts.
RUN mkdir -p /app/data
ENV DATABASE_PATH=/app/data/tasks.db

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Gunicorn = production-ready WSGI server (Flask's built-in server is dev-only)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
