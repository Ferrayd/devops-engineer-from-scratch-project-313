.PHONY: run install help test test-cov lint format check docker-build docker-run docker-stop docker-logs db-up db-down clean dev docker-dev

help:
	@echo "Available commands:"
	@echo "  make dev            - Run frontend and backend simultaneously (development)"
	@echo "  make run            - Run the backend only"
	@echo "  make install        - Install dependencies (Python + Node.js)"
	@echo "  make test           - Run tests"
	@echo "  make test-cov       - Run tests with coverage"
	@echo "  make lint           - Run linter (Ruff)"
	@echo "  make format         - Format code with Ruff"
	@echo "  make check          - Run all checks (lint + test)"
	@echo ""
	@echo "Docker commands:"
	@echo "  make docker-build   - Build production Docker image"
	@echo "  make docker-run     - Run production Docker container"
	@echo "  make docker-dev     - Run development Docker container with volumes"
	@echo "  make docker-stop    - Stop Docker container"
	@echo "  make docker-logs    - View Docker logs"
	@echo ""
	@echo "Database commands:"
	@echo "  make db-up          - Start PostgreSQL in Docker"
	@echo "  make db-down        - Stop PostgreSQL"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Clean up cache files"

install:
	uv sync
	npm install

run:
	uv run uvicorn main:app --host 0.0.0.0 --port 8080 --reload

dev:
	npm run dev

test:
	uv run pytest tests/ -v --tb=short

test-cov:
	uv run pytest tests/ -v --cov=. --cov-report=html

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check . --fix

check: lint test
	@echo "✓ All checks passed!"

docker-build:
	docker build -t short-links-api:latest .

docker-run: db-up
	docker-compose up -d app

docker-dev: db-up
	docker-compose --profile dev up -d app-dev

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f app

db-up:
	docker-compose up -d db

db-down:
	docker-compose down db

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov node_modules dist