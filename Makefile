PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: help venv install format lint test smoke check clean

help:
	@echo "make venv     - create virtualenv"
	@echo "make install  - install project + dev deps"
	@echo "make format   - format code"
	@echo "make lint     - run lint checks"
	@echo "make test     - run tests"
	@echo "make smoke    - run smoke tests (CLI entry point validation)"
	@echo "make check    - full validation"
	@echo "make clean    - remove caches/build artifacts"

venv:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip setuptools wheel

install: venv
	$(BIN)/pip install -e ".[dev]"

format:
	$(BIN)/ruff format .
	$(BIN)/ruff check . --fix

lint:
	$(BIN)/ruff check .

test:
	$(BIN)/pytest

smoke:
	$(BIN)/pytest tests/test_smoke.py -v

check: format lint test
	$(BIN)/python -m build

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info $(VENV)
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete