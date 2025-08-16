.PHONY: help install start stop restart db-start db-stop migrate test clean health-check logs

# Default target
help:
	@echo "TaskWeight Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Environment:"
	@echo "  install      Install dependencies"
	@echo "  setup        Setup development environment (install + db-start + migrate)"
	@echo ""
	@echo "Database:"
	@echo "  db-start     Start database services"
	@echo "  db-stop      Stop database services"
	@echo "  db-restart   Restart database services"
	@echo "  migrate      Run database migrations"
	@echo ""
	@echo "Server:"
	@echo "  start        Start development server"
	@echo "  stop         Stop development server"
	@echo "  restart      Restart development server"
	@echo ""
	@echo "Development:"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage"
	@echo "  lint         Run code linting"
	@echo "  format       Format code with black"
	@echo ""
	@echo "Monitoring:"
	@echo "  health-check Check system health"
	@echo "  logs         View service logs"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean        Clean up temporary files"
	@echo "  reset        Reset entire development environment"

# Environment setup
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

setup: install db-start
	@echo "Waiting for services to be ready..."
	sleep 15
	@echo "Running migrations..."
	./scripts/migrate.sh
	@echo "Development environment is ready!"

# Database commands
db-start:
	@echo "Starting database services..."
	./scripts/start-db.sh

db-stop:
	@echo "Stopping database services..."
	./scripts/stop-db.sh

db-restart: db-stop db-start

# Server commands
start:
	@echo "Starting development server..."
	./scripts/start-server.sh

# Migration commands
migrate:
	@echo "Running database migrations..."
	./scripts/migrate.sh

# Testing commands
test:
	@echo "Running tests..."
	pytest

test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=app --cov-report=html

# Code quality commands
lint:
	@echo "Running code linting..."
	flake8 app/ --max-line-length=88 --extend-ignore=E203,W503

format:
	@echo "Formatting code..."
	black app/ --line-length=88

# Monitoring commands
health-check:
	@echo "Checking system health..."
	./scripts/health-check.sh

logs:
	@echo "Viewing service logs..."
	docker-compose -f docker-compose.dev.yml logs -f

# Maintenance commands
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

reset: clean db-stop
	@echo "Removing Docker volumes..."
	docker-compose -f docker-compose.dev.yml down -v
	@echo "Removing virtual environment..."
	rm -rf venv/
	@echo "Development environment reset complete"
	@echo "Run 'make setup' to recreate the environment"
