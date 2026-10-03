"""Catalog management and workflow registry for Spec Kit Workflows."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from specify_cli.network import client, resolve_mirror_url
from specify_cli.workflows.models import WorkflowDefinition


@dataclass
class CatalogSource:
    """Configured catalog source item."""

    url: str
    name: str = "default"
    priority: int = 1
    install_allowed: bool = True
    description: str = ""


@dataclass
class WorkflowCatalogEntry:
    """Entry describing a workflow in a catalog."""

    id: str
    name: str
    description: str = ""
    author: str = ""
    version: str = "1.0.0"
    url: str = ""
    tags: list[str] = field(default_factory=list)
    bundled: bool = False
    catalog_name: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], catalog_name: str = "default"
    ) -> WorkflowCatalogEntry:
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            version=str(data.get("version", "1.0.0")),
            url=str(data.get("url", "")),
            tags=list(data.get("tags", []))
            if isinstance(data.get("tags"), list)
            else [],
            bundled=bool(data.get("bundled", False)),
            catalog_name=catalog_name,
        )


def _find_bundled_workflows_dir() -> Path | None:
    """Find bundled workflows directory from local repo checkout or wheel package."""
    # 1. From local source checkout
    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[3]
    if (repo_root / "workflows" / "catalog.json").is_file():
        return repo_root / "workflows"

    # 2. From package _bundled_core
    bundled_core = current_file.parents[1] / "_bundled_core" / "workflows"
    if (bundled_core / "catalog.json").is_file():
        return bundled_core

    return None


class WorkflowCatalog:
    """Manages fetching, caching, and querying workflow catalogs."""

    DEFAULT_CATALOG_URL = (
        "https://raw.githubusercontent.com/github/spec-kit/main/workflows/catalog.json"
    )
    COMMUNITY_CATALOG_URL = "https://raw.githubusercontent.com/github/spec-kit/main/workflows/catalog.community.json"
    CACHE_DURATION = 3600  # 1 hour

    def __init__(self, project_root: Path | None = None, mirror: str | None = None):
        self.project_root = (project_root or Path.cwd()).resolve()
        self.mirror = mirror
        self.cache_dir = self.project_root / ".specify" / "workflows" / ".cache"

    def get_active_catalogs(self) -> list[CatalogSource]:
        """Resolve ordered catalog sources."""
        # 1. Env override
        if env_url := os.environ.get("SPECKIT_WORKFLOW_CATALOG_URL"):
            return [CatalogSource(url=env_url.strip(), name="env-override", priority=1)]

        # 2. Project config .specify/workflow-catalogs.yml
        proj_cfg = self.project_root / ".specify" / "workflow-catalogs.yml"
        if proj_cfg.exists():
            sources = self._load_sources_from_yaml(proj_cfg)
            if sources:
                return sources

        # 3. User config ~/.specify/workflow-catalogs.yml
        user_cfg = Path.home() / ".specify" / "workflow-catalogs.yml"
        if user_cfg.exists():
            sources = self._load_sources_from_yaml(user_cfg)
            if sources:
                return sources

        # 4. Built-in defaults
        return [
            CatalogSource(
                url=self.DEFAULT_CATALOG_URL,
                name="default",
                priority=1,
                install_allowed=True,
                description="Official Spec Kit workflows",
            ),
            CatalogSource(
                url=self.COMMUNITY_CATALOG_URL,
                name="community",
                priority=2,
                install_allowed=False,
                description="Community Spec Kit workflows",
            ),
        ]

    def _load_sources_from_yaml(self, path: Path) -> list[CatalogSource]:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            raw_cats = data.get("catalogs", [])
            sources: list[CatalogSource] = []
            for idx, c in enumerate(raw_cats):
                if isinstance(c, dict) and "url" in c:
                    sources.append(
                        CatalogSource(
                            url=str(c["url"]).strip(),
                            name=str(c.get("name", f"catalog-{idx + 1}")),
                            priority=int(c.get("priority", idx + 1)),
                            install_allowed=bool(c.get("install_allowed", True)),
                            description=str(c.get("description", "")),
                        )
                    )
            sources.sort(key=lambda s: s.priority)
            return sources
        except Exception:
            return []

    def fetch_catalog_data(self, source: CatalogSource) -> dict[str, Any]:
        """Fetch catalog data using local bundled fallback or remote cache."""
        # Check bundled first for official catalogs
        bundled_dir = _find_bundled_workflows_dir()
        if bundled_dir:
            if (
                source.url == self.DEFAULT_CATALOG_URL
                and (bundled_dir / "catalog.json").exists()
            ):
                return json.loads(
                    (bundled_dir / "catalog.json").read_text(encoding="utf-8")
                )
            if (
                source.url == self.COMMUNITY_CATALOG_URL
                and (bundled_dir / "catalog.community.json").exists()
            ):
                return json.loads(
                    (bundled_dir / "catalog.community.json").read_text(encoding="utf-8")
                )

        # Check disk cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        url_hash = hashlib.sha256(source.url.encode("utf-8")).hexdigest()[:16]
        cache_file = self.cache_dir / f"catalog-{url_hash}.json"

        if cache_file.exists():
            mtime = cache_file.stat().st_mtime
            if (time.time() - mtime) < self.CACHE_DURATION:
                try:
                    return json.loads(cache_file.read_text(encoding="utf-8"))
                except Exception:
                    pass

        # Fetch remotely
        target_url = resolve_mirror_url(source.url, mirror=self.mirror)
        try:
            resp = client.get(target_url, timeout=10.0, follow_redirects=True)
            if resp.status_code == 200:
                data = resp.json()
                cache_file.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
                )
                return data
        except Exception as e:
            if cache_file.exists():
                # Stale cache is better than failing
                return json.loads(cache_file.read_text(encoding="utf-8"))
            if bundled_dir and (bundled_dir / "catalog.json").exists():
                return json.loads(
                    (bundled_dir / "catalog.json").read_text(encoding="utf-8")
                )
            raise RuntimeError(f"Failed to fetch catalog from {target_url}: {e}") from e

        return {}

    def get_all_workflows(self) -> list[WorkflowCatalogEntry]:
        """Get all workflows from all active catalogs."""
        results: dict[str, WorkflowCatalogEntry] = {}
        for source in self.get_active_catalogs():
            try:
                data = self.fetch_catalog_data(source)
                raw_wfs = data.get("workflows", {})
                if isinstance(raw_wfs, dict):
                    for wf_id, wf_info in raw_wfs.items():
                        if isinstance(wf_info, dict) and wf_id not in results:
                            results[wf_id] = WorkflowCatalogEntry.from_dict(
                                wf_info, catalog_name=source.name
                            )
            except Exception:
                continue
        return list(results.values())

    def search(self, query: str = "") -> list[WorkflowCatalogEntry]:
        """Search workflows by ID, name, description, or tags."""
        query = query.strip().lower()
        all_entries = self.get_all_workflows()
        if not query:
            return all_entries

        matched = []
        for entry in all_entries:
            if (
                query in entry.id.lower()
                or query in entry.name.lower()
                or query in entry.description.lower()
                or any(query in tag.lower() for tag in entry.tags)
            ):
                matched.append(entry)
        return matched

    def find_entry(self, workflow_id: str) -> WorkflowCatalogEntry | None:
        """Find a single catalog entry by workflow ID."""
        for entry in self.get_all_workflows():
            if entry.id == workflow_id:
                return entry
        return None


class WorkflowRegistry:
    """Manages locally installed workflows in a project."""

    def __init__(self, project_root: Path | None = None, mirror: str | None = None):
        self.project_root = (project_root or Path.cwd()).resolve()
        self.mirror = mirror
        self.workflows_dir = self.project_root / ".specify" / "workflows"
        self.registry_file = self.workflows_dir / "workflow-registry.json"

    def _load_registry_data(self) -> dict[str, Any]:
        if not self.registry_file.exists():
            return {"workflows": {}}
        try:
            return json.loads(self.registry_file.read_text(encoding="utf-8"))
        except Exception:
            return {"workflows": {}}

    def _save_registry_data(self, data: dict[str, Any]) -> None:
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def list_installed(self) -> list[WorkflowDefinition]:
        """List all installed workflows in .specify/workflows/."""
        installed: list[WorkflowDefinition] = []
        if not self.workflows_dir.exists():
            return installed

        for path in self.workflows_dir.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                wf_file = path / "workflow.yml"
                if not wf_file.exists():
                    wf_file = path / "workflow.yaml"
                if wf_file.exists():
                    try:
                        wf = WorkflowDefinition.from_yaml(wf_file)
                        installed.append(wf)
                    except Exception:
                        continue
        return installed

    def get_installed(self, workflow_id: str) -> WorkflowDefinition | None:
        """Get an installed workflow by ID."""
        wf_dir = self.workflows_dir / workflow_id
        if wf_dir.exists():
            for name in ("workflow.yml", "workflow.yaml"):
                wf_file = wf_dir / name
                if wf_file.exists():
                    return WorkflowDefinition.from_yaml(wf_file)
        return None

    def install(
        self, workflow_id: str, catalog: WorkflowCatalog | None = None
    ) -> WorkflowDefinition:
        """Install a workflow into .specify/workflows/{id}/."""
        catalog = catalog or WorkflowCatalog(self.project_root, mirror=self.mirror)
        entry = catalog.find_entry(workflow_id)

        target_dir = self.workflows_dir / workflow_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "workflow.yml"

        # Check bundled local first
        bundled_dir = _find_bundled_workflows_dir()
        if bundled_dir and (bundled_dir / workflow_id / "workflow.yml").exists():
            src_file = bundled_dir / workflow_id / "workflow.yml"
            shutil.copy2(src_file, target_file)
        elif entry and entry.url:
            # Download from URL
            url = resolve_mirror_url(entry.url, mirror=self.mirror)
            resp = client.get(url, timeout=15.0, follow_redirects=True)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Failed to download workflow from {url}: status {resp.status_code}"
                )
            target_file.write_text(resp.text, encoding="utf-8")
        else:
            raise ValueError(
                f"Workflow '{workflow_id}' not found in catalogs or bundled assets"
            )

        # Update registry JSON
        reg = self._load_registry_data()
        wf_def = WorkflowDefinition.from_yaml(target_file)
        reg["workflows"][workflow_id] = {
            "id": wf_def.id,
            "name": wf_def.name,
            "version": wf_def.version,
            "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "path": str(target_file.relative_to(self.project_root)),
        }
        self._save_registry_data(reg)
        return wf_def

    def uninstall(self, workflow_id: str) -> bool:
        """Uninstall a workflow."""
        wf_dir = self.workflows_dir / workflow_id
        if not wf_dir.exists():
            return False

        shutil.rmtree(wf_dir, ignore_errors=True)
        reg = self._load_registry_data()
        if workflow_id in reg.get("workflows", {}):
            del reg["workflows"][workflow_id]
            self._save_registry_data(reg)
        return True


__all__ = [
    "CatalogSource",
    "WorkflowCatalog",
    "WorkflowCatalogEntry",
    "WorkflowRegistry",
    "_find_bundled_workflows_dir",
]
