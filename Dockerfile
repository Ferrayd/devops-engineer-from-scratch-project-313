FROM python:3.11-slim as python-builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Устанавливаем UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Копируем ВСЕ файлы (включая app/) перед установкой зависимостей
COPY . .

# Теперь uv может найти папку 'app' и установить зависимости
RUN uv sync --frozen --no-dev

# ============================================
# Финальный stage
# ============================================

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем готовое виртуальное окружение из builder stage
COPY --from=python-builder /app/.venv /app/.venv

# Копируем только необходимый код приложения
COPY app ./app
COPY public ./public

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/ping || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]