.PHONY: help install test lint format clean docker-build docker-run

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test: ## Run tests with coverage
	pytest tests/ -v --cov=cybershield --cov-report=term-missing

lint: ## Run linting
	flake8 cybershield tests
	black --check cybershield tests
	mypy cybershield

format: ## Format code
	black cybershield tests
	isort cybershield tests

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/

docker-build: ## Build Docker image
	docker build -t cybershield:latest .

docker-run: ## Run Docker container
	docker run -p 8000:8000 cybershield:latest

run-api: ## Run API server locally
	uvicorn cybershield.api.app:create_app --reload --host 0.0.0.0 --port 8000

run-worker: ## Run background worker
	python -m cybershield.worker

migrate: ## Run database migrations
	alembic upgrade head

db-reset: ## Reset database
	alembic downgrade base
	alembic upgrade head
