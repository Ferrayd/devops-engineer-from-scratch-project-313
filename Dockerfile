FROM python:3.11-slim as python-builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install uv

WORKDIR /tmp

COPY pyproject.toml uv.lock ./

RUN uv venv /opt/venv && \
    /opt/venv/bin/uv pip install -r <(uv pip compile pyproject.toml)

FROM node:20-alpine as frontend-builder

WORKDIR /frontend

COPY package.json package-lock.json ./

RUN npm ci

COPY build-frontend.sh ./

RUN chmod +x build-frontend.sh && ./build-frontend.sh

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nginx \
        supervisor \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

WORKDIR /app

COPY --from=python-builder /opt/venv /opt/venv

COPY main.py config.py models.py database.py schemas.py ./

RUN mkdir -p /app/public

COPY --from=frontend-builder /frontend/dist /app/public

COPY nginx/nginx.conf /etc/nginx/nginx.conf

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN mkdir -p /var/log/supervisor /var/run/supervisor

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/ping || exit 1

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]