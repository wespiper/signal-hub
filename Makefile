.PHONY: help install dev-install test lint format type-check clean

help:
	@echo "Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  dev-install  Install development dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linting"
	@echo "  format       Format code"
	@echo "  type-check   Run type checking"
	@echo "  clean        Clean up generated files"

install:
	poetry install --no-dev

dev-install:
	poetry install
	pre-commit install

test:
	poetry run pytest

lint:
	poetry run ruff check src tests

format:
	poetry run black src tests
	poetry run ruff check --fix src tests

type-check:
	poetry run mypy src

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov .pytest_cache .mypy_cache .ruff_cache