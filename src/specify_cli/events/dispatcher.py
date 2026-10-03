# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Lifecycle event hook discovery and execution for specify-cli-zh."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class EventHook:
    event_name: str
    source: str  # "project", "extension:<id>", "preset:<id>"
    script_path: Path
    description: str = ""
    timeout: int = 60


class EventDispatcher:
    """Discovers and dispatches lifecycle events to registered hooks."""

    KNOWN_EVENTS = [
        "pre-init",
        "post-init",
        "pre-specify",
        "post-specify",
        "pre-plan",
        "post-plan",
        "pre-tasks",
        "post-tasks",
        "pre-implement",
        "post-implement",
        "post-converge",
    ]

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path.cwd()

    def discover_hooks(self, event_filter: str | None = None) -> list[EventHook]:
        """Discover all event hook scripts in the project."""
        hooks: list[EventHook] = []

        # 1. Project-level hooks in .specify/hooks/
        project_hooks_dir = self.project_root / ".specify" / "hooks"
        if project_hooks_dir.is_dir():
            for p in sorted(project_hooks_dir.iterdir()):
                if p.is_file() and not p.name.startswith("."):
                    ev_name = p.stem
                    if not event_filter or ev_name == event_filter:
                        hooks.append(
                            EventHook(
                                event_name=ev_name,
                                source="project",
                                script_path=p,
                                description=f"项目本地钩子: {p.name}",
                            )
                        )

        # 2. Extension hooks from .specify/extensions/
        ext_dir = self.project_root / ".specify" / "extensions"
        if ext_dir.is_dir():
            for ext in ext_dir.iterdir():
                if ext.is_dir() and not ext.name.startswith("."):
                    manifest_file = ext / "extension.yml"
                    if manifest_file.is_file():
                        try:
                            data = yaml.safe_load(
                                manifest_file.read_text(encoding="utf-8")
                            )
                            if isinstance(data, dict):
                                raw_hooks = data.get("hooks", {})
                                if isinstance(raw_hooks, dict):
                                    for ev, script_rel in raw_hooks.items():
                                        if not event_filter or ev == event_filter:
                                            script_path = ext / str(script_rel)
                                            hooks.append(
                                                EventHook(
                                                    event_name=ev,
                                                    source=f"extension:{ext.name}",
                                                    script_path=script_path,
                                                    description=f"来自扩展 {ext.name}",
                                                )
                                            )
                        except Exception:
                            pass

        return hooks

    def run_event(
        self, event_name: str, payload: str = "", timeout: int = 60
    ) -> list[tuple[EventHook, int, str]]:
        """Run all hooks registered for event_name."""
        hooks = self.discover_hooks(event_name)
        results: list[tuple[EventHook, int, str]] = []

        env = os.environ.copy()
        env["SPECIFY_EVENT"] = event_name
        env["SPECIFY_PROJECT_ROOT"] = str(self.project_root)

        for h in hooks:
            if not h.script_path.is_file():
                results.append((h, 127, f"脚本文件不存在: {h.script_path}"))
                continue

            try:
                cmd = [str(h.script_path)]
                if h.script_path.suffix == ".py":
                    cmd = ["python3", str(h.script_path)]
                elif h.script_path.suffix == ".sh":
                    cmd = ["bash", str(h.script_path)]

                proc = subprocess.run(
                    cmd,
                    input=payload,
                    text=True,
                    capture_output=True,
                    cwd=str(self.project_root),
                    timeout=timeout,
                    env=env,
                )
                output = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
                results.append((h, proc.returncode, output.strip()))
            except subprocess.TimeoutExpired:
                results.append((h, 124, f"执行超时 ({timeout}s)"))
            except Exception as e:
                results.append((h, 1, f"执行异常: {e}"))

        return results
