#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DIST_DIR="${1:-$ROOT_DIR/dist/release-packages}"

assets=(
  "spec-kit-template-claude-sh-"
  "spec-kit-template-claude-ps-"
  "spec-kit-template-codex-sh-"
  "spec-kit-template-codex-ps-"
  "spec-kit-template-kiro-cli-sh-"
  "spec-kit-template-kiro-cli-ps-"
  "spec-kit-template-shai-sh-"
  "spec-kit-template-shai-ps-"
  "spec-kit-template-tabnine-sh-"
  "spec-kit-template-tabnine-ps-"
  "spec-kit-template-agy-sh-"
  "spec-kit-template-agy-ps-"
)

printf 'Release assets are expected under %s\n' "$DIST_DIR"
printf 'Core package prefixes:\n'
printf ' - %s\n' "${assets[@]}"
