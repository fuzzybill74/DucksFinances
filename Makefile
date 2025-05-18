.PHONY: help install test lint format clean db-upgrade db-downgrade db-migrate

# Default target
help:
	@echo "Available targets:"
	@echo "  install     Install dependencies and set up the development environment"
	@echo "  test        Run tests"
	@echo "  lint        Run linters"
	@echo "  format      Format code"
	@echo "  clean       Remove temporary files"
	@echo "  db-upgrade  Upgrade database to the latest migration"
	@echo "  db-downgrade  Roll back the last database migration"
	@echo "  db-migrate  Create a new database migration"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r backend/requirements.txt
	@echo "Installing pre-commit hooks..."
	pre-commit install

# Run tests
test:
	@echo "Running tests..."
	cd backend && python -m pytest tests/ -v

# Run linters
lint:
	@echo "Running linters..."
	cd backend && flake8 .
	cd backend && black --check .
	cd backend && isort --check-only .

# Format code
format:
	@echo "Formatting code..."
	cd backend && black .
	cd backend && isort .

# Clean up
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type d -name ".ruff_cache" -exec rm -r {} +
	find . -type f -name "*.py[co]" -delete
	find . -type f -name "*~" -delete

# Database commands
db-upgrade:
	@echo "Upgrading database..."
	cd backend && flask db upgrade

db-downgrade:
	@echo "Downgrading database..."
	cd backend && flask db downgrade

db-migrate:
	@if [ -z "$(m)" ]; then \
		echo "Error: Migration message is required. Usage: make db-migrate m='Your migration message'"; \
		exit 1; \
	fi
	@echo "Creating new database migration..."
	cd backend && flask db migrate -m "$(m)"

# Run the application
run:
	@echo "Starting development server..."
	cd backend && flask run
