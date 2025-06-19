.PHONY: help install dev-install lint format check type-check test clean all sync

# Default target
help:
	@echo "Available commands:"
	@echo "  sync          Sync dependencies from uv.lock"
	@echo "  install       Install production dependencies"
	@echo "  dev-install   Install development dependencies"
	@echo "  lint          Run ruff linting (check only)"
	@echo "  format        Run ruff formatting"
	@echo "  check         Run ruff check and fix issues"
	@echo "  type-check    Run pyright type checking"
	@echo "  test          Run tests with pytest"
	@echo "  all           Run format, check, type-check, and test"
	@echo "  clean         Clean cache files"

# Sync dependencies from lockfile (recommended for development)
sync:
	uv sync

# Install production dependencies only
install:
	uv sync --no-dev

# Install development dependencies (same as sync)
dev-install:
	uv sync

# Run ruff linting (check only, no fixes)
lint:
	uv run ruff check .

# Run ruff formatting
format:
	uv run ruff format .


# Run ruff check with automatic fixes
check:
	uv run ruff check . --fix

# Run pyright type checking
type-check:
	uv run pyright

# Run tests
test:
	uv run pytest tests/ -v

# Run all checks
all: format check type-check test

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true 