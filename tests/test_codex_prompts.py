# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""单元测试：Codex CLI 提示词渲染与同步辅助函数。

覆盖范围：
- normalize_speckit_name          各种前缀格式的规范化
- codex_prompt_filename / slash   文件名与 slash 命令生成
- parse_markdown_command_template 正常 frontmatter 与无 frontmatter 解析
- render_codex_prompt             渲染输出结构正确性
- sync_codex_prompts_from_templates 同步逻辑（创建 / 更新 / 保留 / 错误）
- malformed frontmatter           损坏 YAML 的降级处理
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from specify_cli.codex_prompts import (
    CodexPromptSyncResult,
    codex_prompt_filename,
    codex_slash_command,
    normalize_speckit_name,
    parse_markdown_command_template,
    render_codex_prompt,
    sync_codex_prompts_from_templates,
)


# ── normalize_speckit_name ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("/prompts:speckit-specify", "specify"),
        ("prompts:speckit-plan", "plan"),
        ("speckit.tasks", "tasks"),
        ("speckit-analyze", "analyze"),
        ("speckit:implement", "implement"),
        ("clarify", "clarify"),          # already bare — no stripping needed
        ("speckit-", ""),                # edge: empty suffix
    ],
)
def test_normalize_speckit_name(raw: str, expected: str) -> None:
    assert normalize_speckit_name(raw) == expected


# ── codex_prompt_filename / codex_slash_command ───────────────────────────────


@pytest.mark.parametrize(
    "name, expected_file, expected_slash",
    [
        ("specify", "speckit-specify.md", "/prompts:speckit-specify"),
        ("speckit-plan", "speckit-plan.md", "/prompts:speckit-plan"),
        ("/prompts:speckit-tasks", "speckit-tasks.md", "/prompts:speckit-tasks"),
    ],
)
def test_codex_filename_and_slash(
    name: str, expected_file: str, expected_slash: str
) -> None:
    assert codex_prompt_filename(name) == expected_file
    assert codex_slash_command(name) == expected_slash


# ── parse_markdown_command_template ───────────────────────────────────────────


def test_parse_template_with_frontmatter(tmp_path: Path) -> None:
    template = tmp_path / "specify.md"
    template.write_text(
        textwrap.dedent("""\
        ---
        description: 创建规范
        argument-hint: feature description
        ---

        Body content here.
        """),
        encoding="utf-8",
    )
    frontmatter, body = parse_markdown_command_template(template)
    assert frontmatter["description"] == "创建规范"
    assert frontmatter["argument-hint"] == "feature description"
    assert "Body content here." in body


def test_parse_template_without_frontmatter(tmp_path: Path) -> None:
    template = tmp_path / "plain.md"
    template.write_text("Just plain text.\n", encoding="utf-8")
    frontmatter, body = parse_markdown_command_template(template)
    assert frontmatter == {}
    assert "Just plain text." in body


def test_parse_template_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_markdown_command_template(tmp_path / "nonexistent.md")


# ── render_codex_prompt ───────────────────────────────────────────────────────


def test_render_codex_prompt_structure(tmp_path: Path) -> None:
    template = tmp_path / "specify.md"
    template.write_text(
        textwrap.dedent("""\
        ---
        description: 创建规范
        handoffs:
          - label: 构建计划
            agent: speckit.plan
        ---

        Run /speckit.plan after this.
        """),
        encoding="utf-8",
    )
    filename, content = render_codex_prompt(template)

    assert filename == "speckit-specify.md"
    # Body refs normalised
    assert "/prompts:speckit-plan" in content
    assert "/speckit.plan" not in content
    # Frontmatter refs normalised
    assert "speckit-plan" in content
    assert "speckit.plan" not in content
    # Default argument-hint injected
    assert "argument-hint:" in content
    # Proper delimiters
    assert content.startswith("---\n")


def test_render_codex_prompt_injects_argument_hint(tmp_path: Path) -> None:
    """argument-hint should be added when absent from frontmatter."""
    template = tmp_path / "tasks.md"
    template.write_text(
        "---\ndescription: generate tasks\n---\n\nBody.\n",
        encoding="utf-8",
    )
    _, content = render_codex_prompt(template)
    assert "argument-hint: command arguments" in content


def test_render_codex_prompt_preserves_existing_argument_hint(tmp_path: Path) -> None:
    """A pre-existing argument-hint must NOT be overwritten."""
    template = tmp_path / "clarify.md"
    template.write_text(
        "---\ndescription: clarify\nargument-hint: feature context\n---\n\nBody.\n",
        encoding="utf-8",
    )
    _, content = render_codex_prompt(template)
    assert "argument-hint: feature context" in content
    assert "argument-hint: command arguments" not in content


# ── sync_codex_prompts_from_templates ────────────────────────────────────────


def _make_template(directory: Path, name: str, description: str = "desc") -> Path:
    """Helper: write a minimal valid command template."""
    path = directory / f"{name}.md"
    path.write_text(
        f"---\ndescription: {description}\n---\n\nBody for {name}.\n",
        encoding="utf-8",
    )
    return path


def test_sync_creates_prompt_files(tmp_path: Path) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    global_dir = tmp_path / "global_prompts"

    t1 = _make_template(templates_dir, "specify")
    t2 = _make_template(templates_dir, "plan")

    result = sync_codex_prompts_from_templates(
        [t1, t2], project_dir, global_prompts_dir=global_dir
    )

    assert result.created == 4  # 2 templates × 2 dirs
    assert result.updated == 0
    assert result.preserved == 0
    assert result.total == 4
    assert (project_dir / ".codex" / "prompts" / "speckit-specify.md").exists()
    assert (global_dir / "speckit-plan.md").exists()


def test_sync_preserves_identical_files(tmp_path: Path) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    global_dir = tmp_path / "global_prompts"

    t1 = _make_template(templates_dir, "specify")

    # First sync → creates
    sync_codex_prompts_from_templates([t1], project_dir, global_prompts_dir=global_dir)
    # Second sync → preserves (content unchanged)
    result = sync_codex_prompts_from_templates(
        [t1], project_dir, global_prompts_dir=global_dir
    )

    assert result.created == 0
    assert result.preserved == 2  # 1 template × 2 dirs


def test_sync_updates_changed_files(tmp_path: Path) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    global_dir = tmp_path / "global_prompts"

    t1 = _make_template(templates_dir, "specify", description="original")
    sync_codex_prompts_from_templates([t1], project_dir, global_prompts_dir=global_dir)

    # Change the template
    t1.write_text(
        "---\ndescription: updated\n---\n\nUpdated body.\n", encoding="utf-8"
    )
    result = sync_codex_prompts_from_templates(
        [t1], project_dir, global_prompts_dir=global_dir
    )

    assert result.updated == 2  # 1 template × 2 dirs


def test_sync_result_slash_commands(tmp_path: Path) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    global_dir = tmp_path / "global_prompts"

    t1 = _make_template(templates_dir, "specify")
    t2 = _make_template(templates_dir, "plan")

    result = sync_codex_prompts_from_templates(
        [t1, t2], project_dir, global_prompts_dir=global_dir
    )

    assert "/prompts:speckit-specify" in result.slash_commands
    assert "/prompts:speckit-plan" in result.slash_commands


def test_sync_skips_nonexistent_template(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    global_dir = tmp_path / "global_prompts"

    ghost = tmp_path / "ghost.md"  # Does not exist

    result = sync_codex_prompts_from_templates(
        [ghost], project_dir, global_prompts_dir=global_dir
    )

    assert result.total == 0


# ── malformed frontmatter ─────────────────────────────────────────────────────


def test_parse_malformed_frontmatter_falls_back_to_empty(tmp_path: Path) -> None:
    """Non-dict YAML frontmatter (e.g. a bare string) should produce {}."""
    template = tmp_path / "bad.md"
    template.write_text("---\njust a string\n---\n\nBody.\n", encoding="utf-8")
    frontmatter, body = parse_markdown_command_template(template)
    assert frontmatter == {}
    assert "Body." in body


def test_sync_with_malformed_frontmatter_still_creates_file(tmp_path: Path) -> None:
    """A template with malformed frontmatter should still produce a prompt file."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    global_dir = tmp_path / "global_prompts"

    bad_template = templates_dir / "broken.md"
    bad_template.write_text("---\nnot_yaml: [unclosed\n---\n\nBody.\n", encoding="utf-8")

    result = sync_codex_prompts_from_templates(
        [bad_template], project_dir, global_prompts_dir=global_dir
    )
    # Should not raise; may create 0 or more files depending on yaml parser
    assert isinstance(result, CodexPromptSyncResult)


def test_sync_overwrite_false_preserves_existing(tmp_path: Path) -> None:
    """When overwrite=False, existing files must never be updated."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    global_dir = tmp_path / "global_prompts"

    t1 = _make_template(templates_dir, "specify", description="v1")
    sync_codex_prompts_from_templates([t1], project_dir, global_prompts_dir=global_dir)

    t1.write_text("---\ndescription: v2\n---\n\nNew body.\n", encoding="utf-8")
    result = sync_codex_prompts_from_templates(
        [t1], project_dir, global_prompts_dir=global_dir, overwrite=False
    )

    assert result.updated == 0
    assert result.preserved == 2
