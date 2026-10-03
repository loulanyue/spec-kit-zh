# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Bundle subsystem for specify-cli-zh."""

from .catalog import BundleCatalog
from .cli import bundle_app
from .manager import BundleManager
from .models import BundleCatalogEntry, BundleComponentRef, BundleManifest

__all__ = [
    "bundle_app",
    "BundleCatalog",
    "BundleManager",
    "BundleManifest",
    "BundleCatalogEntry",
    "BundleComponentRef",
]
