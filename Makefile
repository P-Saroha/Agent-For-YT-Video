.PHONY: help install dev test lint format clean docker-build docker-run docker-stop

# Variables
PYTHON := python
PIP := pip
DOCKER := docker
DOCKER_COMPOSE := docker-compose

help:
	@echo "AI Content Analysis Platform - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev          - Run development server"
	@echo "  make test         - Run tests with coverage"
	@echo "  make lint         - Run linters (flake8, black check)"
	@echo "  make format       - Format code with black and isort"
	@echo "  make clean        - Clean temporary files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run with Docker Compose"
	@echo "  make docker-stop  - Stop Docker containers"
	@echo "  make requirements - Update requirements.txt"

install:
	@echo "Installing dependencies..."
	$(PIP) install -r server/requirements.txt
	$(PIP) install pytest pytest-cov pytest-asyncio black flake8 isort

dev:
	@echo "Starting development server..."
	cd server && $(PYTHON) start_server.py

test:
	@echo "Running tests with coverage..."
	pytest tests/ -v --cov=server --cov-report=html --cov-report=term

lint:
	@echo "Running linters..."
	flake8 server/ --count --select=E9,F63,F7,F82 --show-source --statistics
	black --check server/
	isort --check-only server/

format:
	@echo "Formatting code..."
	black server/
	isort server/

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info

docker-build:
	@echo "Building Docker image..."
	$(DOCKER) build -t ai-content-assistant:latest .

docker-run:
	@echo "Running with Docker Compose..."
	$(DOCKER_COMPOSE) up -d

docker-stop:
	@echo "Stopping Docker containers..."
	$(DOCKER_COMPOSE) down

docker-logs:
	@echo "Showing Docker logs..."
	$(DOCKER_COMPOSE) logs -f

requirements:
	@echo "Updating requirements.txt..."
	$(PIP) freeze > server/requirements.txt

security:
	@echo "Running security checks..."
	$(PIP) install safety bandit
	safety check
	bandit -r server/
