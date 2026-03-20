#!/usr/bin/env bash
set -euo pipefail

TASK="${1:-}"
if [ -z "$TASK" ]; then
  echo 'Usage: ./scripts/codex-dev.sh "your task"'
  exit 1
fi

if [ ! -f "AGENTS.md" ]; then
  echo "Error: AGENTS.md not found in current directory"
  exit 1
fi

if [ ! -f "Makefile" ]; then
  echo "Error: Makefile not found in current directory"
  exit 1
fi

echo "[1/4] Reviewing repository and planning..."
codex "Read this Python repository and create a concise implementation plan for the following task. Do not modify files yet.

Task: ${TASK}"

echo "[2/4] Implementing changes..."
codex --full-auto "Implement the following task in this Python repository.

Requirements:
- follow AGENTS.md
- make the smallest correct change
- update or add tests as needed
- run: make install || true
- run: make format
- run: make lint
- run: make test
- if validation fails, fix the root cause and rerun
- if packaging/imports are affected, also run: make check

Task: ${TASK}"

echo "[3/4] Final validation..."
make format
make lint
make test

echo "[4/4] Summarizing changes..."
codex "Based on the current repository state and git diff, summarize:
1) what changed
2) which files changed
3) validation results
4) remaining risks
5) one conventional commit message

Only output the summary and the commit message."