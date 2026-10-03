# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Lifecycle events subsystem for specify-cli-zh."""

from .cli import event_app
from .dispatcher import EventDispatcher, EventHook

__all__ = [
    "event_app",
    "EventDispatcher",
    "EventHook",
]
