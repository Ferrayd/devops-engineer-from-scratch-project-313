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

dev: db-up db-wait
	@echo "Starting frontend and backend..."
	npm run dev

test:
	uv run pytest tests/ -v --tb=short

test-cov:
	uv run pytest tests/ -v --cov=. --cov-report=html --cov-report=term
	@echo "✓ Coverage report generated in htmlcov/index.html"

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check . --fix

check: lint test
	@echo "✓ All checks passed!"

docker-build:
	docker build -t short-links-api:latest .
	@echo "✓ Docker image built successfully"

docker-run: db-up db-wait
	docker-compose up -d app
	@echo "✓ Application is running on http://localhost"

docker-dev: db-up db-wait
	docker-compose --profile dev up -d app-dev
	@echo "✓ Development environment is running"

docker-stop:
	docker-compose down
	@echo "✓ Docker containers stopped"

docker-logs:
	docker-compose logs -f app

db-up:
	docker-compose up -d db
	@echo "Starting PostgreSQL..."

db-wait:
	@echo "Waiting for PostgreSQL to be ready..."
	@for i in {1..30}; do \
		if docker exec short_links_db psql -U postgres -c "SELECT 1" > /dev/null 2>&1; then \
			echo "✓ PostgreSQL is ready"; \
			break; \
		fi; \
		echo "Waiting... ($$i/30)"; \
		sleep 1; \
	done

db-down:
	docker-compose down db
	@echo "✓ PostgreSQL stopped"

db-logs:
	docker logs -f short_links_db

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info 2>/dev/null || true
	rm -rf node_modules 2>/dev/null || true
	@echo "✓ Cleanup completed"

setup-dev: clean install
	cp .env.example .env
	@echo "✓ Setup completed"
	@echo "Run 'make dev' to start development"