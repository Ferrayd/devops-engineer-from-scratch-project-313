FROM ghcr.io/astral-sh/uv:latest

WORKDIR /app

RUN apt-get update && \
    apt-get install -y nginx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN uv pip install --no-cache-dir -r requirements.txt

COPY app/ /app/app/
COPY nginx.conf /etc/nginx/sites-available/default
COPY start.sh /app/start.sh

COPY public ./public

RUN mkdir -p /var/log/nginx /var/run/nginx && \
    chmod +x /app/start.sh

EXPOSE 80

CMD ["/app/start.sh"]