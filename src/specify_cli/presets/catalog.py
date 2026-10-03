# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Preset catalog discovery and management."""

from __future__ import annotations

import json
from pathlib import Path

from .models import PresetCatalogEntry, PresetManifest


def _find_bundled_presets_dir() -> Path | None:
    # 1. Dev repo layout: <root>/presets
    root_presets = Path(__file__).resolve().parents[3] / "presets"
    if root_presets.is_dir() and (root_presets / "catalog.json").is_file():
        return root_presets

    # 2. Wheel layout: specify_cli/_bundled_core/presets
    wheel_presets = Path(__file__).resolve().parents[1] / "_bundled_core" / "presets"
    if wheel_presets.is_dir() and (wheel_presets / "catalog.json").is_file():
        return wheel_presets

    return None


class PresetCatalog:
    """Manages preset discovery from bundled, community, and remote catalogs."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path.cwd()
        self.bundled_dir = _find_bundled_presets_dir()

    def list_bundled(self) -> list[PresetCatalogEntry]:
        """Return catalog entries from the bundled presets catalog."""
        if not self.bundled_dir:
            return []
        cat_file = self.bundled_dir / "catalog.json"
        if not cat_file.is_file():
            return []
        try:
            data = json.loads(cat_file.read_text(encoding="utf-8"))
            presets_map = data.get("presets", {})
            entries: list[PresetCatalogEntry] = []
            for pid, pdata in presets_map.items():
                if isinstance(pdata, dict):
                    entries.append(PresetCatalogEntry.from_dict(pdata, entry_id=pid))
            return entries
        except Exception:
            return []

    def list_community(self) -> list[PresetCatalogEntry]:
        """Return catalog entries from the community catalog."""
        if not self.bundled_dir:
            return []
        cat_file = self.bundled_dir / "catalog.community.json"
        if not cat_file.is_file():
            return []
        try:
            data = json.loads(cat_file.read_text(encoding="utf-8"))
            presets_map = data.get("presets", {})
            entries: list[PresetCatalogEntry] = []
            for pid, pdata in presets_map.items():
                if isinstance(pdata, dict):
                    entries.append(PresetCatalogEntry.from_dict(pdata, entry_id=pid))
            return entries
        except Exception:
            return []

    def list_available(self) -> list[PresetCatalogEntry]:
        """Return all available presets (bundled + community, deduplicated)."""
        seen: set[str] = set()
        res: list[PresetCatalogEntry] = []
        for entry in self.list_bundled():
            seen.add(entry.id)
            res.append(entry)
        for entry in self.list_community():
            if entry.id not in seen:
                seen.add(entry.id)
                res.append(entry)
        return res

    def search(self, query: str) -> list[PresetCatalogEntry]:
        """Search available presets by ID, name, description, or tags."""
        q = query.lower().strip()
        all_presets = self.list_available()
        if not q:
            return all_presets

        results: list[PresetCatalogEntry] = []
        for p in all_presets:
            if (
                q in p.id.lower()
                or q in p.name.lower()
                or q in p.description.lower()
                or any(q in t.lower() for t in p.tags)
            ):
                results.append(p)
        return results

    def get_info(self, preset_id: str) -> PresetCatalogEntry | None:
        """Find catalog entry by preset ID."""
        for p in self.list_available():
            if p.id == preset_id:
                return p
        return None

    def get_bundled_manifest(self, preset_id: str) -> PresetManifest | None:
        """Load manifest from bundled presets directory."""
        if not self.bundled_dir:
            return None
        candidate = self.bundled_dir / preset_id / "preset.yml"
        if candidate.is_file():
            return PresetManifest.from_yaml(candidate)
        return None
