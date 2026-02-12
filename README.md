### Hexlet tests and linter status:
[![Actions Status](https://github.com/Ferrayd/devops-engineer-from-scratch-project-313/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/Ferrayd/devops-engineer-from-scratch-project-313/actions)
[![CI](https://github.com/Ferrayd/devops-engineer-from-scratch-project-313/actions/workflows/ci.yml/badge.svg)](https://github.com/Ferrayd/devops-engineer-from-scratch-project-313/actions/workflows/ci.yml)

# Сокращатель ссылок, 

Проект который позволяет превратить длинный URL-адрес в короткий код и использовать его для быстрого перехода.

## Стек технологий

- **Backend:** FastAPI, SQLModel, AsyncIO
- **Database:** PostgreSQL (продакшен), SQLite (разработка)
- **Frontend:** Vue.js (поставляется в npm пакете)
- **Testing:** pytest, pytest-asyncio
- **Linting:** Ruff
- **CI/CD:** GitHub Actions
- **Deployment:** Render

## Требования

- Python 3.11+
- Node.js 20+ (для фронтенда)
- Docker и Docker Compose (опционально)

## Быстрый старт

### Локальная разработка

1. Клонирование репозитория

git clone https://github.com/YOUR_USERNAME/short-links-api.git

cd short-links-api
2. Установка зависимостей

make install
3. Копирование конфигурации

cp .env.example .env
4. Запуск фронтенда и бэкенда

make dev

Приложение будет доступно на:
- **UI:** http://localhost:5173
- **API:** http://localhost:8080
- **API Docs:** http://localhost:8080/docs

### Запуск только бэкенда

make run

Бэкенд будет доступен на `http://localhost:8080`

## API Endpoints

### Получить все ссылки (с пагинацией)

GET /api/links?range=[0,10]

**Параметры:**
- `range` (optional): Диапазон в формате `[start,end]`, например `[0,10]`

**Пример ответа:**

[
    {
        “id”: 1,
        “original_url”: “https://example.com/long-url”,
        “short_name”: “exmpl”,
        “short_url”: “http://localhost:8080/r/exmpl”
    }
]

**Заголовки ответа:**
- `Content-Range: links 0-9/42` - диапазон и общее количество
- `Accept-Ranges: links` - поддержка пагинации

### Создать ссылку

POST /api/links

Content-Type: application/json

{
    “original_url”: “https://example.com/very-long-url”,
    “short_name”: “exmpl”
}

**Ответ (201 Created):**

{

    “id”: 1,

    “original_url”: “https://example.com/very-long-url”,

    “short_name”: “exmpl”,

    “short_url”: “http://localhost:8080/r/exmpl”,

    “created_at”: “2024-01-15T10:30:00”

}

### Получить ссылку по ID

GET /api/links/{id}
**Ответ (200 OK):**
{

    “id”: 1,

    “original_url”: “https://example.com/very-long-url”,

    “short_name”: “exmpl”,

    “short_url”: “http://localhost:8080/r/exmpl”,

    “created_at”: “2024-01-15T10:30:00”

}

### Обновить ссылку

PUT /api/links/{id}

Content-Type: application/json

{

    “original_url”: “https://example.com/updated-url”,

    “short_name”: “updated”

}
**Ответ (200 OK):**

{

    “id”: 1,

    “original_url”: “https://example.com/updated-url”,

    “short_name”: “updated”,

    “short_url”: “http://localhost:8080/r/updated”,

    “created_at”: “2024-01-15T10:30:00”

}

### Удалить ссылку

DELETE /api/links/{id}

**Ответ (204 No Content)**

### Проверка здоровья

GET /ping

**Ответ:** `"pong"`

## Тестирование

### Запуск тестов

make test

### Запуск с отчетом о покрытии

make test-cov

Отчет будет в `htmlcov/index.html`

### Проверка кода

Только проверка

make lint
Автоматическое форматирование

make format
Все проверки

make check

## Docker

### Запуск в Docker (разработка)

make docker-dev

Приложение доступно на `http://localhost:8080`

### Запуск в Docker (продакшен)

make docker-build

make docker-run

Приложение доступно на `http://localhost`

### Просмотр логов

make docker-logs

## Развертывание на Render

### 1. Подготовка

1. Создайте аккаунт на [render.com](https://render.com)
2. Создайте PostgreSQL базу данных
3. Скопируйте `DATABASE_URL`

### 2. Создание Web Service

1. Создайте новый **Web Service**
2. Подключите ваш GitHub репозиторий
3. Установите **Environment Variables:**

DATABASE_URL=postgresql://…your-database-url

SHORT_URL_BASE=https://your-app.onrender.com

ENVIRONMENT=production

CORS_ORIGINS=[“https://your-app.onrender.com”]

PORT=80

4. **Build Command:**

pip install uv && uv pip install -r <(uv pip compile pyproject.toml) && npm install && npm run build

5. **Start Command:**

/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

6. **Health Check URL:**

/ping

### 3. Деплой

Деплой произойдет автоматически при push в основную ветку.

## Переменные окружения

| Переменная | Описание | Для разработки | Для продакшена |
|---|---|---|---|
| `DATABASE_URL` | URL подключения к БД | `sqlite:///./database.db` | `postgresql://...` |
| `SHORT_URL_BASE` | Базовый URL для коротких ссылок | `http://localhost:8080` | `https://your-domain.com` |
| `ENVIRONMENT` | Окружение | `development` | `production` |
| `CORS_ORIGINS` | Допустимые origins для CORS | `["http://localhost:5173"]` | `["https://your-domain.com"]` |
| `PORT` | Порт сервера | `8080` | `80` |