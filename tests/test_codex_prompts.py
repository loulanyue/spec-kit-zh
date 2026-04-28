from specify_cli.codex_prompts import (
    codex_slash_command,
    render_codex_prompt,
    sync_codex_prompts_from_templates,
)


def test_render_codex_prompt_normalizes_command_examples(tmp_path):
    template = tmp_path / "specify.md"
    template.write_text(
        "---\n"
        "description: test\n"
        "---\n\n"
        "Use /speckit.plan, /speckit:tasks, and /speckit-implement next.\n",
        encoding="utf-8",
    )

    filename, rendered = render_codex_prompt(template)

    assert filename == "speckit-specify.md"
    assert "/prompts:speckit-plan" in rendered
    assert "/prompts:speckit-tasks" in rendered
    assert "/prompts:speckit-implement" in rendered


def test_sync_codex_prompts_updates_existing_generated_files(tmp_path):
    template = tmp_path / "plan.md"
    template.write_text("---\ndescription: test\n---\n\nPlan body\n", encoding="utf-8")
    project = tmp_path / "project"
    project.mkdir()
    global_dir = tmp_path / "global-prompts"
    stale = project / ".codex" / "prompts" / "speckit-plan.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale", encoding="utf-8")

    result = sync_codex_prompts_from_templates([template], project, global_prompts_dir=global_dir)

    assert result.updated == 1
    assert result.created == 1
    assert stale.read_text(encoding="utf-8") != "stale"
    assert (global_dir / "speckit-plan.md").exists()
    assert result.slash_commands == (codex_slash_command("plan"),)
