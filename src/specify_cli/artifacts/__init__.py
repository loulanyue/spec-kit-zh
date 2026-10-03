# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Artifact subsystem for specify-cli-zh."""

from .cli import artifact_app
from .inspector import ArtifactInspector, ArtifactItem

__all__ = [
    "artifact_app",
    "ArtifactInspector",
    "ArtifactItem",
]
