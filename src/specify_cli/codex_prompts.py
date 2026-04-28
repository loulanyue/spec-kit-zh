"""Codex prompt rendering and synchronization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import re
import yaml


CODEX_ARGUMENT_HINT = "command arguments"
DEFAULT_CODEX_PROMPTS_DIR = Path.home() / ".codex" / "prompts"


@dataclass(frozen=True)
class CodexPromptSyncResult:
    """Summary for a Codex prompt synchronization run."""

    project_prompts_dir: Path
    global_prompts_dir: Path
    command_names: tuple[str, ...]
    created: int = 0
    updated: int = 0
    preserved: int = 0

    @property
    def total(self) -> int:
        return self.created + self.updated + self.preserved

    @property
    def slash_commands(self) -> tuple[str, ...]:
        return tuple(codex_slash_command(command) for command in self.command_names)


def parse_markdown_command_template(template_path: Path) -> tuple[dict, str]:
    """Parse a markdown command template into frontmatter and body."""
    content = template_path.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
            if not isinstance(frontmatter, dict):
                frontmatter = {}
            return frontmatter, parts[2].strip() + "\n"
    return {}, content


def normalize_speckit_name(name: str) -> str:
    """Normalize a speckit-prefixed command or skill name to its bare command name."""
    if name.startswith("/prompts:speckit-"):
        return name[len("/prompts:speckit-") :]
    if name.startswith("prompts:speckit-"):
        return name[len("prompts:speckit-") :]
    if name.startswith("speckit."):
        return name[len("speckit.") :]
    if name.startswith("speckit-"):
        return name[len("speckit-") :]
    if name.startswith("speckit:"):
        return name[len("speckit:") :]
    return name


def codex_prompt_filename(command_name: str) -> str:
    """Return the Codex prompt filename for a bare command name."""
    return f"speckit-{normalize_speckit_name(command_name)}.md"


def codex_slash_command(command_name: str) -> str:
    """Return the Codex slash command exposed by a prompt filename."""
    return f"/prompts:speckit-{normalize_speckit_name(command_name)}"


def _replace_speckit_frontmatter_refs(value):
    """Convert dot-style speckit refs to hyphen-style refs for prompt metadata."""
    if isinstance(value, str):
        return value.replace("speckit.", "speckit-").replace("speckit:", "speckit-")
    if isinstance(value, list):
        return [_replace_speckit_frontmatter_refs(item) for item in value]
    if isinstance(value, dict):
        return {key: _replace_speckit_frontmatter_refs(item) for key, item in value.items()}
    return value


def _replace_speckit_body_refs(body: str) -> str:
    """Normalize in-prompt command examples to Codex namespace syntax."""
    return re.sub(r"/speckit[.:-]([A-Za-z0-9_-]+)", r"/prompts:speckit-\1", body)


def render_codex_prompt(template_path: Path) -> tuple[str, str]:
    """Render a command template into a Codex-friendly slash-command prompt file."""
    command_name = template_path.stem
    frontmatter, body = parse_markdown_command_template(template_path)
    rendered_frontmatter = _replace_speckit_frontmatter_refs(dict(frontmatter))
    rendered_frontmatter.setdefault("argument-hint", CODEX_ARGUMENT_HINT)
    frontmatter_text = yaml.safe_dump(rendered_frontmatter, sort_keys=False, allow_unicode=True).strip()
    content = f"---\n{frontmatter_text}\n---\n\n{_replace_speckit_body_refs(body).rstrip()}\n"
    return codex_prompt_filename(command_name), content


def sync_codex_prompts_from_templates(
    command_templates: Iterable[Path],
    project_path: Path,
    *,
    global_prompts_dir: Path = DEFAULT_CODEX_PROMPTS_DIR,
    overwrite: bool = True,
) -> CodexPromptSyncResult:
    """Synchronize Codex prompts into project-local and global prompt directories."""
    templates = tuple(sorted(command_templates))
    project_prompts_dir = project_path / ".codex" / "prompts"
    target_dirs = (project_prompts_dir, global_prompts_dir)
    created = 0
    updated = 0
    preserved = 0
    command_names: list[str] = []

    for target_dir in target_dirs:
        target_dir.mkdir(parents=True, exist_ok=True)
        for template_file in templates:
            command_names.append(template_file.stem)
            filename, rendered = render_codex_prompt(template_file)
            destination = target_dir / filename
            if destination.exists():
                if overwrite and destination.read_text(encoding="utf-8") != rendered:
                    destination.write_text(rendered, encoding="utf-8")
                    updated += 1
                else:
                    preserved += 1
            else:
                destination.write_text(rendered, encoding="utf-8")
                created += 1

    unique_command_names = tuple(dict.fromkeys(command_names))
    return CodexPromptSyncResult(
        project_prompts_dir=project_prompts_dir,
        global_prompts_dir=global_prompts_dir,
        command_names=unique_command_names,
        created=created,
        updated=updated,
        preserved=preserved,
    )
