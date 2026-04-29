#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUTPUT_DIR="${1:-$ROOT_DIR/dist/release-packages}"
VERSION="${VERSION:-$(python3 - <<'PY'
from pathlib import Path
import re
text = Path("pyproject.toml").read_text(encoding="utf-8")
match = re.search(r'^version = "([^"]+)"', text, re.M)
print(match.group(1) if match else "0.0.0")
PY
)}"

ALL_AGENTS=(
  agy amp auggie bob claude codebuddy codex copilot cursor-agent gemini
  generic kiro-cli kilocode opencode qodercli qwen roo shai tabnine vibe windsurf
)
ALL_SCRIPTS=(sh ps)

package_root_for_agent() {
  case "$1" in
    copilot) echo ".github/agents" ;;
    codex) echo ".codex/prompts" ;;
    windsurf) echo ".windsurf/workflows" ;;
    kilocode) echo ".kilocode/workflows" ;;
    agy) echo ".agent/workflows" ;;
    kiro-cli) echo ".kiro/prompts" ;;
    opencode) echo ".opencode/command" ;;
    tabnine) echo ".tabnine/agent/commands" ;;
    *) echo ".$1/commands" ;;
  esac
}

mkdir -p "$OUTPUT_DIR"

for agent in "${ALL_AGENTS[@]}"; do
  for script_kind in "${ALL_SCRIPTS[@]}"; do
    stage_dir="$OUTPUT_DIR/spec-kit-template-${agent}-${script_kind}-${VERSION}"
    package_dir="$stage_dir/.specify"
    rm -rf "$stage_dir"
    mkdir -p "$package_dir/templates" "$package_dir/scripts/bash" "$package_dir/scripts/powershell"

    cp -R "$ROOT_DIR/templates/." "$package_dir/templates/"
    cp -R "$ROOT_DIR/scripts/bash/." "$package_dir/scripts/bash/"
    cp -R "$ROOT_DIR/scripts/powershell/." "$package_dir/scripts/powershell/"

    target_dir="$stage_dir/$(package_root_for_agent "$agent")"
    mkdir -p "$target_dir"

    if [[ "$agent" == "tabnine" ]]; then
      cat > "$target_dir/speckit-plan.toml" <<'EOF'
prompt = "See .specify/templates/commands/plan.md"
args = "{{args}}"
EOF
    else
      cp "$ROOT_DIR/templates/commands/plan.md" "$target_dir/speckit-plan.md"
    fi

    (
      cd "$OUTPUT_DIR"
      zip -qr "spec-kit-template-${agent}-${script_kind}-${VERSION}.zip" "spec-kit-template-${agent}-${script_kind}-${VERSION}"
    )
    rm -rf "$stage_dir"
  done
done
