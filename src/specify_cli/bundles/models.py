# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Bundle models and data structures for specify-cli-zh."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class BundleComponentRef:
    id: str
    version: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BundleComponentRef:
        return cls(
            id=str(data.get("id", "")),
            version=str(data.get("version", "")),
        )


@dataclass
class BundleManifest:
    id: str
    name: str
    version: str
    description: str
    author: str
    role: str = "developer"
    license: str = "MIT"
    requires_speckit: str = ""
    provides_extensions: list[BundleComponentRef] = field(default_factory=list)
    provides_workflows: list[BundleComponentRef] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    manifest_path: Path | None = None

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], manifest_path: Path | None = None
    ) -> BundleManifest:
        raw_b = data.get("bundle", data)
        bid = str(raw_b.get("id", ""))
        name = str(raw_b.get("name", bid))
        version = str(raw_b.get("version", "1.0.0"))
        description = str(raw_b.get("description", ""))
        author = str(raw_b.get("author", ""))
        role = str(raw_b.get("role", "developer"))
        license_str = str(raw_b.get("license", "MIT"))

        reqs = data.get("requires", {})
        req_ver = str(reqs.get("speckit_version", "")) if isinstance(reqs, dict) else ""

        provides = data.get("provides", {})
        exts: list[BundleComponentRef] = []
        wfs: list[BundleComponentRef] = []

        if isinstance(provides, dict):
            for e in provides.get("extensions", []):
                if isinstance(e, dict):
                    exts.append(BundleComponentRef.from_dict(e))
            for w in provides.get("workflows", []):
                if isinstance(w, dict):
                    wfs.append(BundleComponentRef.from_dict(w))

        tags = [str(t) for t in data.get("tags", raw_b.get("tags", []))]

        return cls(
            id=bid,
            name=name,
            version=version,
            description=description,
            author=author,
            role=role,
            license=license_str,
            requires_speckit=req_ver,
            provides_extensions=exts,
            provides_workflows=wfs,
            tags=tags,
            manifest_path=manifest_path,
        )

    @classmethod
    def from_yaml(cls, path: Path) -> BundleManifest:
        if not path.is_file():
            raise FileNotFoundError(f"Bundle manifest not found: {path}")
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ValueError(f"Invalid YAML document in bundle manifest: {path}")
        return cls.from_dict(data, manifest_path=path)


@dataclass
class BundleCatalogEntry:
    id: str
    name: str
    version: str
    description: str
    author: str
    role: str = "developer"
    bundled: bool = False
    tags: list[str] = field(default_factory=list)
    download_url: str = ""
    repository: str = ""
    requires_speckit: str = ""
    provides_extensions: int = 0
    provides_workflows: int = 0
    verified: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any], entry_id: str = "") -> BundleCatalogEntry:
        bid = entry_id or str(data.get("id", ""))
        name = str(data.get("name", bid))
        version = str(data.get("version", "1.0.0"))
        description = str(data.get("description", ""))
        author = str(data.get("author", ""))
        role = str(data.get("role", "developer"))
        bundled = bool(data.get("bundled", False))
        tags = [str(t) for t in data.get("tags", [])]
        download_url = str(data.get("download_url", ""))
        repository = str(data.get("repository", ""))
        verified = bool(data.get("verified", False))

        reqs = data.get("requires", {})
        req_ver = str(reqs.get("speckit_version", "")) if isinstance(reqs, dict) else ""

        provides = data.get("provides", {})
        num_exts = 0
        num_wfs = 0
        if isinstance(provides, dict):
            num_exts = (
                int(provides.get("extensions", 0))
                if isinstance(provides.get("extensions"), int)
                else len(provides.get("extensions", []))
            )
            num_wfs = (
                int(provides.get("workflows", 0))
                if isinstance(provides.get("workflows"), int)
                else len(provides.get("workflows", []))
            )

        return cls(
            id=bid,
            name=name,
            version=version,
            description=description,
            author=author,
            role=role,
            bundled=bundled,
            tags=tags,
            download_url=download_url,
            repository=repository,
            requires_speckit=req_ver,
            provides_extensions=num_exts,
            provides_workflows=num_wfs,
            verified=verified,
        )
