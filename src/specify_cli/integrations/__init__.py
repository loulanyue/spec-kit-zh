# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""AI assistant integrations subsystem for specify-cli-zh."""

from .cli import integration_app
from .manager import EXTENDED_AGENTS, IntegrationManager

__all__ = [
    "integration_app",
    "IntegrationManager",
    "EXTENDED_AGENTS",
]
