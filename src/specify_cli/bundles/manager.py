# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Bundle installation, uninstallation, and lifecycle management."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .catalog import BundleCatalog, _find_bundled_bundles_dir
from .models import BundleManifest


class BundleManager:
    """Manages bundle installation, component orchestrations, and registry."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path.cwd()
        self.bundles_dir = self.project_root / ".specify" / "bundles"
        self.catalog = BundleCatalog(self.project_root)

    def _ensure_dir(self) -> None:
        self.bundles_dir.mkdir(parents=True, exist_ok=True)

    def _read_registry(self) -> dict[str, dict[str, object]]:
        reg_file = self.bundles_dir / ".registry"
        if not reg_file.is_file():
            return {}
        try:
            data = json.loads(reg_file.read_text(encoding="utf-8"))
            return data.get("bundles", {})
        except Exception:
            return {}

    def _write_registry(self, bundles_data: dict[str, dict[str, object]]) -> None:
        self._ensure_dir()
        reg_file = self.bundles_dir / ".registry"
        content = json.dumps({"bundles": bundles_data}, indent=2, ensure_ascii=False)
        reg_file.write_text(content, encoding="utf-8")

    def list_installed(self) -> list[BundleManifest]:
        """List all installed bundles in project."""
        if not self.bundles_dir.is_dir():
            return []
        manifests: list[BundleManifest] = []
        for b in self.bundles_dir.iterdir():
            if b.is_dir() and not b.name.startswith("."):
                manifest_file = b / "bundle.yml"
                if manifest_file.is_file():
                    try:
                        manifests.append(BundleManifest.from_yaml(manifest_file))
                    except Exception:
                        pass
        return manifests

    def get_installed(self, bundle_id: str) -> BundleManifest | None:
        candidate = self.bundles_dir / bundle_id / "bundle.yml"
        if candidate.is_file():
            return BundleManifest.from_yaml(candidate)
        return None

    def install(self, bundle_id: str, force: bool = False) -> BundleManifest:
        """Install a bundle and orchestrate its required extensions and workflows."""
        self._ensure_dir()
        target_dir = self.bundles_dir / bundle_id

        if target_dir.exists() and not force:
            raise FileExistsError(
                f"Bundle '{bundle_id}' 已安装。如需重新安装请使用 --force。"
            )

        bundled_dir = _find_bundled_bundles_dir()
        if not bundled_dir or not (bundled_dir / bundle_id).is_dir():
            raise FileNotFoundError(
                f"未找到 Bundle '{bundle_id}'，且无法从内置源获取。"
            )

        source_dir = bundled_dir / bundle_id
        if target_dir.exists():
            shutil.rmtree(target_dir)

        shutil.copytree(source_dir, target_dir)
        manifest = BundleManifest.from_yaml(target_dir / "bundle.yml")

        # 1. Install provided extensions if available
        try:
            from specify_cli.extensions import ExtensionManager

            ext_mgr = ExtensionManager(self.project_root)
            for ext_ref in manifest.provides_extensions:
                try:
                    ext_mgr.install(ext_ref.id, force=force)
                except Exception:
                    pass
        except Exception:
            pass

        # 2. Install provided workflows if available
        try:
            from specify_cli.workflows.catalog import WorkflowRegistry

            wf_reg = WorkflowRegistry(self.project_root)
            for wf_ref in manifest.provides_workflows:
                try:
                    wf_reg.install(wf_ref.id)
                except Exception:
                    pass
        except Exception:
            pass

        # 3. Update registry
        reg = self._read_registry()
        reg[bundle_id] = {
            "name": manifest.name,
            "version": manifest.version,
            "role": manifest.role,
            "extensions": [e.id for e in manifest.provides_extensions],
            "workflows": [w.id for w in manifest.provides_workflows],
        }
        self._write_registry(reg)

        return manifest

    def remove(self, bundle_id: str) -> bool:
        """Uninstall a bundle and remove its associated components."""
        target_dir = self.bundles_dir / bundle_id
        if not target_dir.exists():
            return False

        manifest = self.get_installed(bundle_id)
        if manifest:
            # Uninstall workflows
            try:
                from specify_cli.workflows.catalog import WorkflowRegistry

                wf_reg = WorkflowRegistry(self.project_root)
                for wf_ref in manifest.provides_workflows:
                    try:
                        wf_reg.uninstall(wf_ref.id)
                    except Exception:
                        pass
            except Exception:
                pass

            # Uninstall extensions
            try:
                from specify_cli.extensions import ExtensionManager

                ext_mgr = ExtensionManager(self.project_root)
                for ext_ref in manifest.provides_extensions:
                    try:
                        ext_mgr.remove(ext_ref.id)
                    except Exception:
                        pass
            except Exception:
                pass

        shutil.rmtree(target_dir)

        reg = self._read_registry()
        if bundle_id in reg:
            del reg[bundle_id]
            self._write_registry(reg)

        return True
