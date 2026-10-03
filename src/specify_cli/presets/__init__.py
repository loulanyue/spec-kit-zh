# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Presets subsystem for specify-cli-zh."""

from .catalog import PresetCatalog
from .cli import preset_app
from .manager import PresetManager
from .models import PresetCatalogEntry, PresetManifest, PresetTemplateEntry
from .resolver import PresetResolver

__all__ = [
    "preset_app",
    "PresetCatalog",
    "PresetManager",
    "PresetResolver",
    "PresetManifest",
    "PresetCatalogEntry",
    "PresetTemplateEntry",
]
