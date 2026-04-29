#!/usr/bin/env bash

set -euo pipefail

if command -v uv >/dev/null 2>&1; then
  uv sync
fi

if command -v curl >/dev/null 2>&1; then
  KIRO_INSTALLER_SHA256="7487a65cf310b7fb59b357c4b5e6e3f3259d383f4394ecedb39acf70f307cffb"
  tmp_installer="$(mktemp)"
  curl -fsSL "https://kiro.dev/install.sh" -o "$tmp_installer"
  printf '%s  %s\n' "$KIRO_INSTALLER_SHA256" "$tmp_installer" | sha256sum -c -
  rm -f "$tmp_installer"
fi
