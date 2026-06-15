# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
.PHONY: help venv install format lint typecheck test smoke coverage check link-check docs clean audit

PYTHON ?= python3
VENV   ?= .venv
BIN    := $(VENV)/bin

help:
	@echo "=============================== spec-kit-zh Makefile ==============================="
	@echo ""
	@echo "  开发环境:"
	@echo "    make venv        - 创建 Python 虚拟环境"
	@echo "    make install     - 安装项目及开发依赖"
	@echo "    make clean       - 删除缓存和构建产物"
	@echo ""
	@echo "  代码质量:"
	@echo "    make format      - 使用 ruff 格式化代码"
	@echo "    make lint        - 运行 ruff 代码规范检查"
	@echo "    make typecheck   - 运行 mypy 静态类型检查"
	@echo "    make audit       - 运行依赖安全漏洞扫描 (pip-audit)"
	@echo ""
	@echo "  测试:"
	@echo "    make test        - 运行全量单元测试"
	@echo "    make smoke       - 运行 smoke 测试（CLI 入口验证）"
	@echo "    make coverage    - 运行测试并生成覆盖率报告"
	@echo ""
	@echo "  文档:"
	@echo "    make docs        - 使用 docfx 构建文档站（需先 npm install -g docfx）"
	@echo "    make link-check  - 检查 Markdown 文档中的死链"
	@echo ""
	@echo "  发布:"
	@echo "    make check       - 完整验证流程（format + lint + test）"
	@echo "    make build       - 构建 Python 发行包（wheel + sdist）"
	@echo "===================================================================================="

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

typecheck:
	$(BIN)/mypy src/specify_cli --ignore-missing-imports --no-error-summary

audit:
	@command -v pip-audit >/dev/null 2>&1 || $(BIN)/pip install pip-audit
	$(BIN)/pip-audit --desc

test:
	$(BIN)/pytest

smoke:
	$(BIN)/pytest tests/test_smoke.py -v

coverage:
	$(BIN)/pytest --cov=src/specify_cli --cov-report=term-missing --cov-report=html
	@echo "📊 覆盖率报告已生成至 htmlcov/index.html"

docs:
	@command -v docfx >/dev/null 2>&1 || (echo "请先安装 docfx: npm install -g docfx" && exit 1)
	docfx docs/docfx.json --serve

link-check:
	npx --yes markdown-link-check README.md docs/*.md --config .markdownlint-cli2.jsonc 2>/dev/null || \
	npx --yes markdown-link-check README.md docs/*.md

build:
	$(BIN)/python -m build

check: format lint test build
	@echo "✅ 全量验证通过"

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info htmlcov $(VENV)
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
