"""Codex prompt rendering and synchronization helpers.

This module provides utilities for rendering project command templates into
Codex-compatible slash-command prompt files, and for synchronising those files
into both the project-local ``.codex/prompts/`` directory and the global
``~/.codex/prompts/`` directory.

Typical usage::

    from specify_cli.codex_prompts import sync_codex_prompts_from_templates
    from pathlib import Path

    result = sync_codex_prompts_from_templates(
        command_templates=Path("templates/commands").glob("*.md"),
        project_path=Path("."),
    )
    print(f"Synced {result.total} prompt files.")
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml


CODEX_ARGUMENT_HINT = "command arguments"
DEFAULT_CODEX_PROMPTS_DIR = Path.home() / ".codex" / "prompts"


@dataclass(frozen=True)
class CodexPromptSyncResult:
    """Summary for a Codex prompt synchronization run.

    Attributes:
        project_prompts_dir: Path to the project-local ``.codex/prompts/`` directory.
        global_prompts_dir:  Path to the global ``~/.codex/prompts/`` directory.
        command_names:       Ordered tuple of bare command names that were processed.
        created:             Number of prompt files created from scratch.
        updated:             Number of existing prompt files whose content was updated.
        preserved:           Number of existing prompt files whose content was unchanged.
    """

    project_prompts_dir: Path
    global_prompts_dir: Path
    command_names: tuple[str, ...]
    created: int = 0
    updated: int = 0
    preserved: int = 0

    @property
    def total(self) -> int:
        """Total number of prompt files processed (created + updated + preserved)."""
        return self.created + self.updated + self.preserved

    @property
    def slash_commands(self) -> tuple[str, ...]:
        """Tuple of Codex slash-command strings for all processed commands."""
        return tuple(codex_slash_command(command) for command in self.command_names)


def parse_markdown_command_template(template_path: Path) -> tuple[dict, str]:
    """Parse a markdown command template into frontmatter and body.

    Args:
        template_path: Absolute or relative path to the ``.md`` template file.

    Returns:
        A ``(frontmatter, body)`` tuple where *frontmatter* is a ``dict``
        (empty if the file has no YAML front matter) and *body* is the
        remaining markdown text with leading/trailing whitespace stripped.

    Raises:
        FileNotFoundError: If *template_path* does not exist.
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
    content = template_path.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                frontmatter = {}
            if not isinstance(frontmatter, dict):
                frontmatter = {}
            return frontmatter, parts[2].strip() + "\n"
    return {}, content


def normalize_speckit_name(name: str) -> str:
    """Normalize a speckit-prefixed command or skill name to its bare command name.

    Supported input prefixes:
    - ``/prompts:speckit-``
    - ``prompts:speckit-``
    - ``speckit.``
    - ``speckit-``
    - ``speckit:``

    Args:
        name: A potentially-prefixed command name string.

    Returns:
        The bare command name with any recognized prefix stripped.
    """
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
    """Return the Codex prompt filename for a bare command name.

    Args:
        command_name: A bare or prefixed command name (e.g. ``"specify"``).

    Returns:
        The filename used in ``.codex/prompts/`` (e.g. ``"speckit-specify.md"``).
    """
    return f"speckit-{normalize_speckit_name(command_name)}.md"


def codex_slash_command(command_name: str) -> str:
    """Return the Codex slash command exposed by a prompt filename.

    Args:
        command_name: A bare or prefixed command name.

    Returns:
        The full Codex slash-command string (e.g. ``"/prompts:speckit-specify"``).
    """
    return f"/prompts:speckit-{normalize_speckit_name(command_name)}"


def _replace_speckit_frontmatter_refs(value: object) -> object:
    """Convert dot-style and colon-style speckit refs to hyphen-style for prompt metadata.

    This ensures that YAML front matter values like ``speckit.plan`` or
    ``speckit:plan`` are normalised to ``speckit-plan`` so Codex can resolve
    them as proper slash-command references.

    Args:
        value: A YAML-decoded value (``str``, ``list``, ``dict``, or other).

    Returns:
        The same structure with speckit refs normalised.
    """
    if isinstance(value, str):
        return value.replace("speckit.", "speckit-").replace("speckit:", "speckit-")
    if isinstance(value, list):
        return [_replace_speckit_frontmatter_refs(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_speckit_frontmatter_refs(item) for key, item in value.items()
        }
    return value


def _replace_speckit_body_refs(body: str) -> str:
    """Normalize in-prompt command examples to Codex namespace syntax.

    Replaces any ``/speckit.cmd``, ``/speckit-cmd``, or ``/speckit:cmd``
    occurrences with the canonical ``/prompts:speckit-cmd`` form.

    Args:
        body: The raw markdown body text of the template.

    Returns:
        The body with all speckit command references normalised.
    """
    return re.sub(r"/speckit[.:-]([A-Za-z0-9_-]+)", r"/prompts:speckit-\1", body)


def render_codex_prompt(template_path: Path) -> tuple[str, str]:
    """Render a command template into a Codex-friendly slash-command prompt file.

    Parses the YAML frontmatter, normalises speckit references in both
    frontmatter and body, injects the default ``argument-hint`` if absent,
    then reassembles the file with correct ``---`` delimiters.

    Args:
        template_path: Path to the source ``.md`` command template.

    Returns:
        A ``(filename, content)`` tuple where *filename* is the target prompt
        filename (e.g. ``"speckit-specify.md"``) and *content* is the rendered
        file text ready to be written to disk.
    """
    command_name = template_path.stem
    frontmatter, body = parse_markdown_command_template(template_path)
    rendered_frontmatter = _replace_speckit_frontmatter_refs(dict(frontmatter))
    rendered_frontmatter.setdefault("argument-hint", CODEX_ARGUMENT_HINT)
    frontmatter_text = yaml.safe_dump(
        rendered_frontmatter, sort_keys=False, allow_unicode=True
    ).strip()
    content = (
        f"---\n{frontmatter_text}\n---\n\n{_replace_speckit_body_refs(body).rstrip()}\n"
    )
    return codex_prompt_filename(command_name), content


def sync_codex_prompts_from_templates(
    command_templates: Iterable[Path],
    project_path: Path,
    *,
    global_prompts_dir: Path = DEFAULT_CODEX_PROMPTS_DIR,
    overwrite: bool = True,
) -> CodexPromptSyncResult:
    """Synchronize Codex prompts into project-local and global prompt directories.

    For each template in *command_templates*, renders the Codex prompt and
    writes it to both ``<project_path>/.codex/prompts/`` and
    *global_prompts_dir*.  When *overwrite* is ``True`` (the default) stale
    files are updated; when ``False`` existing files are always preserved.

    Args:
        command_templates: Iterable of paths to ``.md`` command templates.
        project_path:      Root of the project being initialised.
        global_prompts_dir: Override for the global Codex prompts directory
                            (default: ``~/.codex/prompts``).
        overwrite:         If ``True``, overwrite existing files whose content
                           has changed.  If ``False``, never overwrite.

    Returns:
        A :class:`CodexPromptSyncResult` summarising the sync operation.

    Raises:
        OSError: If a target prompt directory cannot be created.
    """
    templates = tuple(sorted(command_templates))
    project_prompts_dir = project_path / ".codex" / "prompts"
    target_dirs = (project_prompts_dir, global_prompts_dir)
    created = 0
    updated = 0
    preserved = 0
    command_names: list[str] = []

    for target_dir in target_dirs:
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Failed to create target directory {target_dir}: {e}") from e

        for template_file in templates:
            if not template_file.exists():
                continue
            command_names.append(template_file.stem)
            filename, rendered = render_codex_prompt(template_file)
            destination = target_dir / filename
            try:
                if destination.exists():
                    if (
                        overwrite
                        and destination.read_text(encoding="utf-8") != rendered
                    ):
                        destination.write_text(rendered, encoding="utf-8")
                        updated += 1
                    else:
                        preserved += 1
                else:
                    destination.write_text(rendered, encoding="utf-8")
                    created += 1
            except IOError as e:
                sys.stderr.write(
                    f"Warning: Failed to write Codex prompt to {destination}: {e}\n"
                )

    unique_command_names = tuple(dict.fromkeys(command_names))
    return CodexPromptSyncResult(
        project_prompts_dir=project_prompts_dir,
        global_prompts_dir=global_prompts_dir,
        command_names=unique_command_names,
        created=created,
        updated=updated,
        preserved=preserved,
    )
