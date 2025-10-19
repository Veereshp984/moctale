.PHONY: install dev lint format test

install:
	poetry install --no-interaction

dev:
	poetry run uvicorn app.main:app --reload --port 8000

lint:
	poetry run ruff check app tests
	poetry run black --check app tests

format:
	poetry run black app tests
	poetry run ruff check --fix app tests

test:
	poetry run pytest
