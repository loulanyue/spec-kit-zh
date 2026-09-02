"""Unit tests for UTF-8 encoding support in ExtensionManifest and ExtensionRegistry."""

import json
from pathlib import Path
import pytest
from specify_cli.extensions import ExtensionManifest, ExtensionRegistry, ValidationError


def test_manifest_loads_unicode_characters(tmp_path: Path):
    """Ensure extension manifest with Chinese characters and emoji loads cleanly."""
    manifest_file = tmp_path / "extension.yml"
    manifest_content = """schema_version: "1.0"
extension:
  id: "ai-workflow-ext"
  name: "AI 工作流扩展 🚀"
  version: "1.0.0"
  description: "面向复杂场景的 Spec-Driven 自动化扩展插件"
  author: "loulanyue"
requires:
  speckit_version: ">=0.9.0"
provides:
  commands:
    - name: "speckit.ai-workflow-ext.plan-zh"
      file: "commands/plan_zh.md"
      description: "执行中文任务规划"
"""
    manifest_file.write_text(manifest_content, encoding="utf-8")

    manifest = ExtensionManifest(manifest_file)
    assert manifest.data["extension"]["name"] == "AI 工作流扩展 🚀"
    assert manifest.data["extension"]["description"] == "面向复杂场景的 Spec-Driven 自动化扩展插件"
    assert manifest.data["provides"]["commands"][0]["description"] == "执行中文任务规划"


def test_registry_persists_unicode_without_escape(tmp_path: Path):
    """Ensure registry persists Chinese metadata in UTF-8 without unicode escapes."""
    ext_dir = tmp_path / ".specify" / "extensions"
    registry = ExtensionRegistry(ext_dir)
    metadata = {
        "version": "1.0.0",
        "name": "中文扩展测试",
        "description": "这是中文描述",
    }
    registry.add("chinese-ext", metadata)

    registry_file = ext_dir / ".registry"
    assert registry_file.exists()

    raw_text = registry_file.read_text(encoding="utf-8")
    assert "中文扩展测试" in raw_text
    assert "这是中文描述" in raw_text

    reloaded = ExtensionRegistry(ext_dir)
    assert "chinese-ext" in reloaded.list()
    assert reloaded.get("chinese-ext")["name"] == "中文扩展测试"
