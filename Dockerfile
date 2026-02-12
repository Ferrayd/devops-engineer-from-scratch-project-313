FROM python:3.11-slim as python-builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir \
        fastapi==0.104.0 \
        uvicorn[standard]==0.24.0 \
        sqlmodel==0.0.14 \
        psycopg2-binary==2.9.0 \
        asyncpg==0.29.0 \
        python-dotenv==1.0.0 \
        pydantic-settings==2.1.0 \
        aiosqlite==0.19.0

FROM node:20-alpine as frontend-builder

WORKDIR /frontend

COPY package.json package-lock.json ./

RUN npm ci

RUN mkdir -p /app/public && \
    cp -r node_modules/@hexlet/project-devops-deploy-crud-frontend/dist/* /app/public/ 2>/dev/null || true

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/*

WORKDIR /app

COPY --from=python-builder /opt/venv /opt/venv

COPY main.py config.py models.py database.py schemas.py ./

COPY --from=frontend-builder /app/public /app/public

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/ping || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]