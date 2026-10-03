# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Artifact scanner and inspector for specify-cli-zh."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ArtifactItem:
    name: str
    artifact_type: str  # "spec", "plan", "tasks", "constitution", "checklist", "other"
    path: Path
    relative_path: str
    size_bytes: int
    modified_time: str
    feature_name: str = ""
    tasks_total: int = 0
    tasks_completed: int = 0


class ArtifactInspector:
    """Discovers and inspects project SDD artifacts."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path.cwd()

    def _determine_type(self, path: Path) -> str:
        stem = path.stem.lower()
        if "spec" in stem:
            return "spec"
        if "plan" in stem:
            return "plan"
        if "task" in stem:
            return "tasks"
        if "constitution" in stem:
            return "constitution"
        if "check" in stem:
            return "checklist"
        return "other"

    def _count_tasks(self, content: str) -> tuple[int, int]:
        total = len(re.findall(r"^\s*-\s*\[[ xX]\]", content, flags=re.MULTILINE))
        completed = len(re.findall(r"^\s*-\s*\[[xX]\]", content, flags=re.MULTILINE))
        return total, completed

    def list_artifacts(self) -> list[ArtifactItem]:
        """Scan project for markdown artifacts."""
        items: list[ArtifactItem] = []

        scan_dirs = [
            self.project_root / ".specify",
            self.project_root / "specs",
            self.project_root / ".specs",
        ]

        # Also search top-level features/ or specs/
        for d in self.project_root.glob("**/spec.md"):
            if ".git" not in d.parts and ".venv" not in d.parts:
                scan_dirs.append(d.parent)

        seen_paths: set[Path] = set()

        for base_dir in scan_dirs:
            if not base_dir.is_dir():
                continue
            for p in base_dir.rglob("*.md"):
                if p in seen_paths or ".git" in p.parts or ".venv" in p.parts:
                    continue
                seen_paths.add(p)
                try:
                    stat = p.stat()
                    content = p.read_text(encoding="utf-8", errors="ignore")
                    tot, comp = self._count_tasks(content)
                    mtime = datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).strftime("%Y-%m-%d %H:%M")

                    feat = ""
                    for part in p.relative_to(self.project_root).parts:
                        if part not in (
                            ".specify",
                            "templates",
                            "memory",
                            "workflows",
                            "presets",
                            "extensions",
                        ):
                            feat = part
                            break

                    items.append(
                        ArtifactItem(
                            name=p.name,
                            artifact_type=self._determine_type(p),
                            path=p,
                            relative_path=str(p.relative_to(self.project_root)),
                            size_bytes=stat.st_size,
                            modified_time=mtime,
                            feature_name=feat,
                            tasks_total=tot,
                            tasks_completed=comp,
                        )
                    )
                except Exception:
                    pass

        return sorted(items, key=lambda x: x.relative_path)
