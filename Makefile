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
	@echo "  make run              Run backend only"
	@echo "  make install          Install dependencies"
	@echo "  make setup            Setup development environment"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test             Run all tests"
	@echo "  make test-cov         Run tests with coverage"
	@echo "  make lint             Check code with Ruff"
	@echo "  make format           Format code with Ruff"
	@echo "  make check            Run all checks"
	@echo ""

install:
	@echo "Installing dependencies..."
	@python -m pip install --upgrade pip
	@python -m pip install --no-cache-dir uv
	@uv pip install --python $(shell which python) --no-cache-dir \
		fastapi==0.104.0 \
		uvicorn[standard]==0.24.0 \
		sqlmodel==0.0.14 \
		psycopg[binary]==3.1.15 \
		asyncpg==0.29.0 \
		python-dotenv==1.0.0 \
		pydantic-settings==2.1.0 \
		aiosqlite==0.19.0 \
		pytest==7.4.0 \
		pytest-asyncio==0.21.0 \
		pytest-cov==4.1.0 \
		httpx==0.25.0 \
		ruff==0.1.0
	@npm install
	@echo "✓ Installation completed"

run:
	@echo "Starting backend server..."
	@echo "Backend: http://localhost:8080"
	@uvicorn main:app --host 0.0.0.0 --port 8080 --reload

dev: install
	@echo "Starting frontend and backend..."
	@npm run dev

test:
	@echo "Running tests..."
	@pytest tests/ -v --tb=short
	@echo "✓ Tests completed"

test-cov:
	@echo "Running tests with coverage..."
	@pytest tests/ -v --cov=. --cov-report=html --cov-report=term
	@echo "✓ Coverage report generated"

lint:
	@echo "Checking code with Ruff..."
	@ruff check .
	@echo "✓ Linting passed"

format:
	@echo "Formatting code with Ruff..."
	@ruff format .
	@ruff check . --fix
	@echo "✓ Code formatted"

check: lint test
	@echo "✓ All checks passed!"

docker-build:
	@echo "Building Docker image..."
	@docker build -t short-links-api:latest .
	@echo "✓ Docker image built"

docker-run:
	@echo "Starting Docker container..."
	@docker-compose up -d app
	@echo "✓ Container started on http://localhost"

docker-stop:
	@echo "Stopping Docker containers..."
	@docker-compose down
	@echo "✓ Containers stopped"

docker-logs:
	@docker-compose logs -f app

db-up:
	@echo "Starting PostgreSQL..."
	@docker-compose up -d db
	@echo "✓ PostgreSQL started"

db-wait:
	@echo "Waiting for PostgreSQL..."
	@for i in {1..30}; do \
		if docker exec short_links_db psql -U postgres -c "SELECT 1" > /dev/null 2>&1; then \
			echo "✓ PostgreSQL ready"; \
			break; \
		fi; \
		sleep 1; \
	done

db-down:
	@echo "Stopping PostgreSQL..."
	@docker-compose down db
	@echo "✓ PostgreSQL stopped"

db-logs:
	@docker logs -f short_links_db

clean:
	@echo "Cleaning up..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info 2>/dev/null || true
	@echo "✓ Cleanup completed"

setup: clean install
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env"; \
	else \
		echo "⚠ .env already exists"; \
	fi
	@echo ""
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
		echo "✓ Created .env"; \
	else \
		echo "⚠ .env already exists"; \
	fi
	@echo ""
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