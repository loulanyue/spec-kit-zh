# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Preset installation, uninstallation, and lifecycle management."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .catalog import PresetCatalog, _find_bundled_presets_dir
from .models import PresetManifest


class PresetManager:
    """Manages preset installation, uninstallation, and local registry."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path.cwd()
        self.presets_dir = self.project_root / ".specify" / "presets"
        self.catalog = PresetCatalog(self.project_root)

    def _ensure_dir(self) -> None:
        self.presets_dir.mkdir(parents=True, exist_ok=True)

    def _read_registry(self) -> dict[str, dict[str, object]]:
        reg_file = self.presets_dir / ".registry"
        if not reg_file.is_file():
            return {}
        try:
            data = json.loads(reg_file.read_text(encoding="utf-8"))
            return data.get("presets", {})
        except Exception:
            return {}

    def _write_registry(self, presets_data: dict[str, dict[str, object]]) -> None:
        self._ensure_dir()
        reg_file = self.presets_dir / ".registry"
        content = json.dumps({"presets": presets_data}, indent=2, ensure_ascii=False)
        reg_file.write_text(content, encoding="utf-8")

    def list_installed(self) -> list[PresetManifest]:
        """List all installed presets."""
        if not self.presets_dir.is_dir():
            return []
        manifests: list[PresetManifest] = []
        for p in self.presets_dir.iterdir():
            if p.is_dir() and not p.name.startswith("."):
                manifest_file = p / "preset.yml"
                if manifest_file.is_file():
                    try:
                        manifests.append(PresetManifest.from_yaml(manifest_file))
                    except Exception:
                        pass
        return manifests

    def get_installed(self, preset_id: str) -> PresetManifest | None:
        """Get an installed preset by ID."""
        candidate = self.presets_dir / preset_id / "preset.yml"
        if candidate.is_file():
            return PresetManifest.from_yaml(candidate)
        return None

    def install(
        self,
        preset_id: str,
        priority: int = 10,
        force: bool = False,
        dev_path: Path | None = None,
    ) -> PresetManifest:
        """Install a preset from local dev path or bundled catalog."""
        self._ensure_dir()
        target_dir = self.presets_dir / preset_id

        if target_dir.exists() and not force:
            raise FileExistsError(
                f"预设 '{preset_id}' 已安装。如需覆盖请使用 --force。"
            )

        if dev_path:
            source_dir = dev_path
            if not (source_dir / "preset.yml").is_file():
                raise FileNotFoundError(
                    f"指定的本地预设目录不存在有效的 preset.yml: {dev_path}"
                )
        else:
            bundled_dir = _find_bundled_presets_dir()
            if not bundled_dir or not (bundled_dir / preset_id).is_dir():
                raise FileNotFoundError(
                    f"未找到预设 '{preset_id}'，且无法从内置源获取。"
                )
            source_dir = bundled_dir / preset_id

        if target_dir.exists():
            shutil.rmtree(target_dir)

        shutil.copytree(source_dir, target_dir)

        manifest = PresetManifest.from_yaml(target_dir / "preset.yml")

        # Update registry
        reg = self._read_registry()
        reg[preset_id] = {
            "priority": priority,
            "enabled": True,
            "version": manifest.version,
            "name": manifest.name,
        }
        self._write_registry(reg)

        return manifest

    def remove(self, preset_id: str) -> bool:
        """Uninstall a preset."""
        target_dir = self.presets_dir / preset_id
        if not target_dir.exists():
            return False

        shutil.rmtree(target_dir)

        reg = self._read_registry()
        if preset_id in reg:
            del reg[preset_id]
            self._write_registry(reg)

        return True

    def update(self, preset_id: str, force: bool = True) -> PresetManifest:
        """Reinstall a preset to latest bundled version."""
        reg = self._read_registry()
        prio = 10
        if preset_id in reg and isinstance(reg[preset_id], dict):
            prio = int(reg[preset_id].get("priority", 10))  # type: ignore
        return self.install(preset_id, priority=prio, force=force)
