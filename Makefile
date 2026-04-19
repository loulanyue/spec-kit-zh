PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: help venv install format lint test smoke check link-check clean

help:
	@echo "make venv       - create virtualenv"
	@echo "make install    - install project + dev deps"
	@echo "make format     - format code"
	@echo "make lint       - run lint checks"
	@echo "make test       - run tests"
	@echo "make smoke      - run smoke tests (CLI entry point validation)"
	@echo "make check      - full validation"
	@echo "make link-check - check for broken links in Markdown docs"
	@echo "make clean      - remove caches/build artifacts"

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

link-check:
	npx --yes markdown-link-check README.md docs/*.md --config .markdownlint-cli2.jsonc 2>/dev/null || \
	npx --yes markdown-link-check README.md docs/*.md

check: format lint test
	$(BIN)/python -m build

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info $(VENV)
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
