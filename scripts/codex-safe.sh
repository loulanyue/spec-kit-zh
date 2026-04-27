#!/usr/bin/env bash
# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
set -euo pipefail

TASK="${1:-}"
if [ -z "$TASK" ]; then
  echo 'Usage: ./scripts/codex-safe.sh "your task"'
  exit 1
fi

codex "Read this Python repository and produce:
1) a short implementation plan,
2) the files likely to change,
3) risks and assumptions.
Do not modify any files yet.

Task: ${TASK}"