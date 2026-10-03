# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Template resolution and composition across project layers."""

from __future__ import annotations

import json
from pathlib import Path


def _normalize_priority(value: object) -> int:
    if isinstance(value, bool):
        return 10
    try:
        p = int(value)  # type: ignore
        return p if p >= 1 else 10
    except (TypeError, ValueError, OverflowError):
        return 10


class PresetResolver:
    """Walks the template priority stack and composes content."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path.cwd()

    def get_installed_preset_ids(self) -> list[str]:
        """Returns preset IDs ordered by priority (lower number = higher precedence)."""
        presets_dir = self.project_root / ".specify" / "presets"
        if not presets_dir.is_dir():
            return []

        registry = presets_dir / ".registry"
        if registry.is_file():
            try:
                data = json.loads(registry.read_text(encoding="utf-8"))
                presets = data.get("presets", {})
                return [
                    pid
                    for pid, meta in sorted(
                        presets.items(),
                        key=lambda kv: (
                            _normalize_priority(kv[1].get("priority"))
                            if isinstance(kv[1], dict)
                            else 10,
                            kv[0],
                        ),
                    )
                    if isinstance(meta, dict) and bool(meta.get("enabled", True))
                ]
            except Exception:
                pass

        try:
            return sorted(
                p.name
                for p in presets_dir.iterdir()
                if p.is_dir() and not p.name.startswith(".")
            )
        except OSError:
            return []

    def resolve_template(self, template_name: str) -> Path | None:
        """Find the winning template file path across all layers."""
        base = self.project_root / ".specify" / "templates"

        # 1. Local project override
        override = base / "overrides" / f"{template_name}.md"
        if override.is_file():
            return override

        # 2. Installed presets (sorted by priority)
        presets_dir = self.project_root / ".specify" / "presets"
        if presets_dir.is_dir():
            for pid in self.get_installed_preset_ids():
                p_dir = presets_dir / pid
                for candidate in (
                    p_dir / "templates" / f"{template_name}.md",
                    p_dir / f"{template_name}.md",
                ):
                    if candidate.is_file():
                        return candidate

        # 3. Extensions
        ext_dir = self.project_root / ".specify" / "extensions"
        if ext_dir.is_dir():
            for ext in sorted(ext_dir.iterdir()):
                if ext.is_dir() and not ext.name.startswith("."):
                    for candidate in (
                        ext / "templates" / f"{template_name}.md",
                        ext / f"{template_name}.md",
                    ):
                        if candidate.is_file():
                            return candidate

        # 4. Core templates
        core = base / f"{template_name}.md"
        if core.is_file():
            return core

        return None

    def resolve_content(self, template_name: str) -> str | None:
        """Resolve and compose template content."""
        target_path = self.resolve_template(template_name)
        if not target_path or not target_path.is_file():
            return None
        return target_path.read_text(encoding="utf-8")
