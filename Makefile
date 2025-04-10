.PHONY: install build test clean dev-deps infra-up infra-down up down

DOCKER_EXEC := podman  # podman or docker

# Install development dependencies
dev-deps:
	uv sync

# Infrastructure services
infra-up:
	$(DOCKER_EXEC) compose up -d mysql redis

infra-down:
	$(DOCKER_EXEC) compose down

# Main installation commands
install: dev-deps infra-up
	@echo "🚀 Project initialization complete!"
	@echo "💡 Tips:"
	@echo "1. Use 'make up' to start all services"
	@echo "2. Use 'make down' to stop all services"

# Docker related commands
build:
	$(DOCKER_EXEC) compose build

up:
	$(DOCKER_EXEC) compose up -d

down:
	$(DOCKER_EXEC) compose down -v

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".coverage*" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +
	find . -type d -name "dist" -exec rm -r {} +
	find . -type d -name "build" -exec rm -r {} +
	find . -type d -name ".eggs" -exec rm -r {} +

update-version:
	uv run python scripts/update-version.py

pre-commit-check:
	uv run pre-commit run --all-files | cat
