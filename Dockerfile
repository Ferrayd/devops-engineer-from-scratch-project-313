FROM python:3.14-slim AS builder

WORKDIR /app

RUN pip install uv

COPY requirements.txt .

RUN uv venv

RUN . .venv/bin/activate && uv pip install --no-cache-dir -r requirements.txt


FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y nginx supervisor && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv

COPY app/ /app/app/
COPY requirements.txt /app/
COPY nginx.conf /etc/nginx/sites-available/default
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY public ./public

RUN mkdir -p /var/log/nginx /var/log/supervisor /var/log/uvicorn /var/run/nginx

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 80

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]