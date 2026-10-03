# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Preset models and manifest parsers for specify-cli-zh."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PresetTemplateEntry:
    type: str  # "template", "command", "script"
    name: str
    file: str
    description: str = ""
    replaces: str = ""
    strategy: str = "replace"  # "replace", "prepend", "append", "wrap"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PresetTemplateEntry:
        return cls(
            type=str(data.get("type", "template")),
            name=str(data.get("name", "")),
            file=str(data.get("file", "")),
            description=str(data.get("description", "")),
            replaces=str(data.get("replaces", "")),
            strategy=str(data.get("strategy", "replace")).lower(),
        )


@dataclass
class PresetManifest:
    id: str
    name: str
    version: str
    description: str
    author: str
    repository: str = ""
    license: str = "MIT"
    requires_speckit: str = ""
    provides_templates: list[PresetTemplateEntry] = field(default_factory=list)
    provides_commands: list[PresetTemplateEntry] = field(default_factory=list)
    provides_scripts: list[PresetTemplateEntry] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    manifest_path: Path | None = None

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], manifest_path: Path | None = None
    ) -> PresetManifest:
        raw_preset = data.get("preset", data)
        preset_id = str(raw_preset.get("id", ""))
        name = str(raw_preset.get("name", preset_id))
        version = str(raw_preset.get("version", "1.0.0"))
        description = str(raw_preset.get("description", ""))
        author = str(raw_preset.get("author", ""))
        repository = str(raw_preset.get("repository", ""))
        license_str = str(raw_preset.get("license", "MIT"))

        reqs = data.get("requires", {})
        requires_speckit = ""
        if isinstance(reqs, dict):
            requires_speckit = str(reqs.get("speckit_version", ""))

        provides = data.get("provides", {})
        templates: list[PresetTemplateEntry] = []
        commands: list[PresetTemplateEntry] = []
        scripts: list[PresetTemplateEntry] = []

        if isinstance(provides, dict):
            raw_tpls = provides.get("templates", [])
            if isinstance(raw_tpls, list):
                for item in raw_tpls:
                    if isinstance(item, dict):
                        entry = PresetTemplateEntry.from_dict(item)
                        if entry.type == "command":
                            commands.append(entry)
                        elif entry.type == "script":
                            scripts.append(entry)
                        else:
                            templates.append(entry)

            raw_cmds = provides.get("commands", [])
            if isinstance(raw_cmds, list):
                for item in raw_cmds:
                    if isinstance(item, dict):
                        commands.append(PresetTemplateEntry.from_dict(item))

            raw_scripts = provides.get("scripts", [])
            if isinstance(raw_scripts, list):
                for item in raw_scripts:
                    if isinstance(item, dict):
                        scripts.append(PresetTemplateEntry.from_dict(item))

        tags = [str(t) for t in data.get("tags", raw_preset.get("tags", []))]

        return cls(
            id=preset_id,
            name=name,
            version=version,
            description=description,
            author=author,
            repository=repository,
            license=license_str,
            requires_speckit=requires_speckit,
            provides_templates=templates,
            provides_commands=commands,
            provides_scripts=scripts,
            tags=tags,
            manifest_path=manifest_path,
        )

    @classmethod
    def from_yaml(cls, path: Path) -> PresetManifest:
        if not path.is_file():
            raise FileNotFoundError(f"Preset manifest not found: {path}")
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ValueError(f"Invalid YAML document in preset manifest: {path}")
        return cls.from_dict(data, manifest_path=path)


@dataclass
class PresetCatalogEntry:
    id: str
    name: str
    version: str
    description: str
    author: str
    bundled: bool = False
    tags: list[str] = field(default_factory=list)
    requires_speckit: str = ""
    download_url: str = ""
    repository: str = ""
    license: str = "MIT"
    provides_commands: int = 0
    provides_templates: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any], entry_id: str = "") -> PresetCatalogEntry:
        pid = entry_id or str(data.get("id", ""))
        name = str(data.get("name", pid))
        version = str(data.get("version", "1.0.0"))
        description = str(data.get("description", ""))
        author = str(data.get("author", ""))
        bundled = bool(data.get("bundled", False))
        tags = [str(t) for t in data.get("tags", [])]
        reqs = data.get("requires", {})
        req_ver = str(reqs.get("speckit_version", "")) if isinstance(reqs, dict) else ""
        download_url = str(data.get("download_url", ""))
        repository = str(data.get("repository", ""))
        license_str = str(data.get("license", "MIT"))

        provides = data.get("provides", {})
        num_cmds = 0
        num_tpls = 0
        if isinstance(provides, dict):
            num_cmds = (
                int(provides.get("commands", 0))
                if isinstance(provides.get("commands"), int)
                else len(provides.get("commands", []))
            )
            num_tpls = (
                int(provides.get("templates", 0))
                if isinstance(provides.get("templates"), int)
                else len(provides.get("templates", []))
            )

        return cls(
            id=pid,
            name=name,
            version=version,
            description=description,
            author=author,
            bundled=bundled,
            tags=tags,
            requires_speckit=req_ver,
            download_url=download_url,
            repository=repository,
            license=license_str,
            provides_commands=num_cmds,
            provides_templates=num_tpls,
        )
