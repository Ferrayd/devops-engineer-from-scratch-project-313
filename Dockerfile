FROM python:3.14-alpine

WORKDIR /app

RUN apk add --no-cache \
    curl \
    nginx && \
    curl -sSL https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:$PATH"

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