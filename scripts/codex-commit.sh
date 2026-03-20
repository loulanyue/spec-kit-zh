#!/usr/bin/env bash
set -euo pipefail

if ! git diff --quiet || ! git diff --cached --quiet; then
  :
else
  echo "No changes to commit."
  exit 0
fi

MSG="$(codex "Look at the current git diff in this Python repository and output exactly one concise conventional commit message. Output only the commit message.")"

git add -A
git commit -m "$MSG"

echo "Committed with message: $MSG"