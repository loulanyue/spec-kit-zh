# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Self-management subsystem for specify-cli-zh."""

from .cli import self_app
from .upgrade import check_latest_version, upgrade_in_place

__all__ = [
    "self_app",
    "check_latest_version",
    "upgrade_in_place",
]
