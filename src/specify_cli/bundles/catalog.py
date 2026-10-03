# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Bundle catalog discovery and queries."""

from __future__ import annotations

import json
from pathlib import Path

from .models import BundleCatalogEntry, BundleManifest


def _find_bundled_bundles_dir() -> Path | None:
    # 1. Dev repo layout: <root>/bundles
    root_bundles = Path(__file__).resolve().parents[3] / "bundles"
    if root_bundles.is_dir() and (root_bundles / "catalog.json").is_file():
        return root_bundles

    # 2. Wheel layout: specify_cli/_bundled_core/bundles
    wheel_bundles = Path(__file__).resolve().parents[1] / "_bundled_core" / "bundles"
    if wheel_bundles.is_dir() and (wheel_bundles / "catalog.json").is_file():
        return wheel_bundles

    return None


class BundleCatalog:
    """Manages bundle discovery from local bundled and community sources."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path.cwd()
        self.bundled_dir = _find_bundled_bundles_dir()

    def list_bundled(self) -> list[BundleCatalogEntry]:
        """List official bundled bundles (e.g. bugfix, assess)."""
        if not self.bundled_dir:
            return []
        cat_file = self.bundled_dir / "catalog.json"
        if not cat_file.is_file():
            return []
        try:
            data = json.loads(cat_file.read_text(encoding="utf-8"))
            bundles_map = data.get("bundles", {})
            entries: list[BundleCatalogEntry] = []
            for bid, bdata in bundles_map.items():
                if isinstance(bdata, dict):
                    entries.append(BundleCatalogEntry.from_dict(bdata, entry_id=bid))
            return entries
        except Exception:
            return []

    def list_community(self) -> list[BundleCatalogEntry]:
        """List community bundles."""
        if not self.bundled_dir:
            return []
        cat_file = self.bundled_dir / "catalog.community.json"
        if not cat_file.is_file():
            return []
        try:
            data = json.loads(cat_file.read_text(encoding="utf-8"))
            bundles_map = data.get("bundles", {})
            entries: list[BundleCatalogEntry] = []
            for bid, bdata in bundles_map.items():
                if isinstance(bdata, dict):
                    entries.append(BundleCatalogEntry.from_dict(bdata, entry_id=bid))
            return entries
        except Exception:
            return []

    def list_available(self) -> list[BundleCatalogEntry]:
        """List all available bundles (bundled + community)."""
        seen: set[str] = set()
        res: list[BundleCatalogEntry] = []
        for b in self.list_bundled():
            seen.add(b.id)
            res.append(b)
        for b in self.list_community():
            if b.id not in seen:
                seen.add(b.id)
                res.append(b)
        return res

    def search(self, query: str) -> list[BundleCatalogEntry]:
        """Search bundles by ID, name, description, or tags."""
        q = query.lower().strip()
        all_bundles = self.list_available()
        if not q:
            return all_bundles

        results: list[BundleCatalogEntry] = []
        for b in all_bundles:
            if (
                q in b.id.lower()
                or q in b.name.lower()
                or q in b.description.lower()
                or any(q in t.lower() for t in b.tags)
            ):
                results.append(b)
        return results

    def get_info(self, bundle_id: str) -> BundleCatalogEntry | None:
        """Find catalog entry for a bundle ID."""
        for b in self.list_available():
            if b.id == bundle_id:
                return b
        return None

    def get_bundled_manifest(self, bundle_id: str) -> BundleManifest | None:
        """Get bundled manifest by bundle ID."""
        if not self.bundled_dir:
            return None
        candidate = self.bundled_dir / bundle_id / "bundle.yml"
        if candidate.is_file():
            return BundleManifest.from_yaml(candidate)
        return None
