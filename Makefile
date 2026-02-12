.PHONY: help install run dev test test-cov lint format check \
        docker-build docker-run docker-dev docker-stop docker-logs \
        db-up db-wait db-down db-logs clean setup-dev version setup

help:
	@echo "╔═══════════════════════════════════════════════════════════╗"
	@echo "║           Short Links API - Available Commands            ║"
	@echo "╚═══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make dev              Run frontend and backend simultaneously"
	@echo "  make run              Run backend only (http://localhost:8080)"
	@echo "  make install          Install dependencies (Python + Node.js)"
	@echo "  make setup            Setup development environment"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test             Run all tests"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make lint             Check code with Ruff"
	@echo "  make format           Format code with Ruff"
	@echo "  make check            Run all checks (lint + test)"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make docker-build     Build production Docker image"
	@echo "  make docker-run       Run production Docker container"
	@echo "  make docker-dev       Run development Docker container"
	@echo "  make docker-stop      Stop Docker containers"
	@echo "  make docker-logs      View Docker logs"
	@echo ""
	@echo "🗄️  Database:"
	@echo "  make db-up            Start PostgreSQL in Docker"
	@echo "  make db-wait          Wait for PostgreSQL to be ready"
	@echo "  make db-down          Stop PostgreSQL"
	@echo "  make db-logs          View PostgreSQL logs"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean            Clean up cache and build files"
	@echo "  make setup-dev        Full setup for development"
	@echo "  make version          Show version information"
	@echo ""

install:
	@echo "Installing dependencies..."
	uv sync
	npm install
	@echo "✓ Installation completed"

run:
	@echo "Starting backend server..."
	@echo "Backend: http://localhost:8080"
	@echo "API Docs: http://localhost:8080/docs"
	uv run uvicorn main:app --host 0.0.0.0 --port 8080 --reload

dev: db-up db-wait
	@echo "Starting frontend and backend..."
	@echo "Frontend: http://localhost:5173"
	@echo "Backend: http://localhost:8080"
	npm run dev

test:
	@echo "Running tests..."
	uv run pytest tests/ -v --tb=short
	@echo "✓ Tests completed"

test-cov:
	@echo "Running tests with coverage..."
	uv run pytest tests/ -v --cov=. --cov-report=html --cov-report=term
	@echo "✓ Coverage report generated in htmlcov/index.html"

lint:
	@echo "Checking code with Ruff..."
	uv run ruff check .
	@echo "✓ Linting passed"

format:
	@echo "Formatting code with Ruff..."
	uv run ruff format .
	uv run ruff check . --fix
	@echo "✓ Code formatted"

check: lint test
	@echo "✓ All checks passed!"

docker-build:
	@echo "Building Docker image..."
	docker build -t short-links-api:latest .
	@echo "✓ Docker image built successfully"

docker-run: db-up db-wait
	@echo "Starting Docker container (production)..."
	docker-compose --profile prod up -d app
	@echo "✓ Application is running on http://localhost"

docker-dev: db-up db-wait
	@echo "Starting Docker container (development)..."
	docker-compose --profile dev up -d app-dev
	@echo "✓ Development environment is running on http://localhost:8080"

docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down
	@echo "✓ Docker containers stopped"

docker-logs:
	docker-compose logs -f app

db-up:
	@echo "Starting PostgreSQL..."
	docker-compose up -d db
	@echo "✓ PostgreSQL started"

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
	@echo "Stopping PostgreSQL..."
	docker-compose down db
	@echo "✓ PostgreSQL stopped"

db-logs:
	docker logs -f short_links_db

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info 2>/dev/null || true
	rm -rf node_modules 2>/dev/null || true
	rm -f database.db 2>/dev/null || true
	@echo "✓ Cleanup completed"

setup: clean install
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env from .env.example"; \
	else \
		echo "⚠ .env already exists, skipping..."; \
	fi
	@echo "✓ Setup completed"
	@echo ""
	@echo "Next steps:"
	@echo "  make dev        - Start development server"
	@echo "  make test       - Run tests"
	@echo "  make check      - Run all checks"
	@echo ""

setup-dev: clean install
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env from .env.example"; \
	else \
		echo "⚠ .env already exists, skipping..."; \
	fi
	@echo "✓ Setup completed"
	@echo ""
	@echo "Next steps:"
	@echo "  make dev        - Start development server"
	@echo "  make test       - Run tests"
	@echo "  make check      - Run all checks"
	@echo ""

version:
	@echo "Short Links API"
	@echo "Version: 1.0.0"
	@echo ""
	@echo "Dependencies:"
	@echo "  Python: $$(python --version 2>&1)"
	@echo "  Node.js: $$(node --version)"
	@echo "  npm: $$(npm --version)"
	@echo ""
	@which docker > /dev/null && echo "  Docker: $$(docker --version)" || echo "  Docker: not installed"
	@which docker-compose > /dev/null && echo "  Docker Compose: $$(docker-compose --version)" || echo "  Docker Compose: not installed"
	@echo ""