.PHONY: help install dev-install test test-unit test-integration lint format type-check check clean build serve serve-pro

# Default target
help:
	@echo "Signal Hub Development Commands"
	@echo "=============================="
	@echo "Setup:"
	@echo "  make install        Install production dependencies"
	@echo "  make dev-install    Install all dependencies including dev"
	@echo ""
	@echo "Development:"
	@echo "  make test          Run all tests with coverage"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make lint          Run linting checks (ruff)"
	@echo "  make format        Format code (black + ruff)"
	@echo "  make type-check    Run type checking (mypy)"
	@echo "  make check         Run all checks (lint + type-check + test)"
	@echo ""
	@echo "Server:"
	@echo "  make serve         Start Signal Hub server (development)"
	@echo "  make serve-pro     Start with Pro features (early access)"
	@echo ""
	@echo "Build & Clean:"
	@echo "  make build         Build distribution packages"
	@echo "  make clean         Clean build artifacts"

# Installation targets
install:
	poetry install --only main

dev-install:
	poetry install
	poetry run pre-commit install

# Testing targets
test:
	poetry run pytest tests/ -v --cov=signal_hub --cov-report=term-missing --cov-report=html

test-unit:
	poetry run pytest tests/unit/ -v

test-integration:
	poetry run pytest tests/integration/ -v

# Code quality targets
lint:
	poetry run ruff check src/ tests/

format:
	poetry run black src/ tests/
	poetry run ruff check --fix src/ tests/

type-check:
	poetry run mypy src/

# Combined check - run all quality checks
check: lint type-check test

# Server targets
serve:
	poetry run signal-hub serve --config config/dev.yaml

serve-pro:
	SIGNAL_HUB_EARLY_ACCESS=true poetry run signal-hub serve --config config/dev.yaml

# Build targets
build: clean
	poetry build

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete