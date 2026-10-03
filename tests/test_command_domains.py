"""Unit tests for the complete set of command domains:

preset, bundle, integration, artifact, event, self.
"""

from __future__ import annotations


from typer.testing import CliRunner

from specify_cli import app
from specify_cli.artifacts import ArtifactInspector
from specify_cli.bundles import BundleCatalog
from specify_cli.events import EventDispatcher
from specify_cli.integrations import IntegrationManager
from specify_cli.presets import PresetCatalog, PresetManager, PresetResolver

runner = CliRunner()


class TestPresetDomain:
    def test_preset_catalog_bundled(self):
        cat = PresetCatalog()
        bundled = cat.list_bundled()
        assert len(bundled) >= 2
        ids = [p.id for p in bundled]
        assert "lean" in ids
        assert "constitution-sync" in ids

    def test_preset_catalog_search(self):
        cat = PresetCatalog()
        res = cat.search("lean")
        assert len(res) >= 1
        assert res[0].id == "lean"

    def test_preset_resolver(self, tmp_path):
        resolver = PresetResolver(project_root=tmp_path)
        # Without any files, resolve returns None
        assert resolver.resolve_template("spec-template") is None

        # Create core template
        core_dir = tmp_path / ".specify" / "templates"
        core_dir.mkdir(parents=True)
        (core_dir / "spec-template.md").write_text("# Core Spec", encoding="utf-8")
        assert (
            resolver.resolve_template("spec-template") == core_dir / "spec-template.md"
        )

        # Create override
        override_dir = core_dir / "overrides"
        override_dir.mkdir()
        (override_dir / "spec-template.md").write_text(
            "# Override Spec", encoding="utf-8"
        )
        assert (
            resolver.resolve_template("spec-template")
            == override_dir / "spec-template.md"
        )

    def test_preset_manager_lifecycle(self, tmp_path):
        mgr = PresetManager(project_root=tmp_path)
        # Create a dummy preset to install via dev
        dev_preset = tmp_path / "my-preset"
        dev_preset.mkdir()
        (dev_preset / "preset.yml").write_text(
            """schema_version: "1.0"
preset:
  id: "test-preset"
  name: "Test Preset"
  version: "1.0.0"
  description: "Test description"
  author: "tester"
provides:
  templates:
    - type: "template"
      name: "custom-template"
      file: "templates/custom.md"
""",
            encoding="utf-8",
        )
        tpl_dir = dev_preset / "templates"
        tpl_dir.mkdir()
        (tpl_dir / "custom.md").write_text("# Custom", encoding="utf-8")

        manifest = mgr.install("test-preset", priority=5, dev_path=dev_preset)
        assert manifest.id == "test-preset"
        assert len(mgr.list_installed()) == 1

        # Test resolver picks up preset
        resolver = PresetResolver(project_root=tmp_path)
        assert "test-preset" in resolver.get_installed_preset_ids()

        # Remove preset
        assert mgr.remove("test-preset") is True
        assert len(mgr.list_installed()) == 0

    def test_preset_cli_commands(self):
        res = runner.invoke(app, ["preset", "list", "--available"])
        assert res.exit_code == 0
        assert "lean" in res.output

        res = runner.invoke(app, ["preset", "search", "lean"])
        assert res.exit_code == 0
        assert "lean" in res.output

        res = runner.invoke(app, ["preset", "info", "lean"])
        assert res.exit_code == 0
        assert "Lean Workflow" in res.output


class TestBundleDomain:
    def test_bundle_catalog(self):
        cat = BundleCatalog()
        bundled = cat.list_bundled()
        assert len(bundled) >= 2
        ids = [b.id for b in bundled]
        assert "bugfix" in ids
        assert "assess" in ids

    def test_bundle_catalog_search(self):
        cat = BundleCatalog()
        res = cat.search("assess")
        assert len(res) >= 1
        assert any(b.id == "assess" for b in res)

    def test_bundle_cli_commands(self):
        res = runner.invoke(app, ["bundle", "list", "--available"])
        assert res.exit_code == 0
        assert "assess" in res.output

        res = runner.invoke(app, ["bundle", "info", "assess"])
        assert res.exit_code == 0
        assert "Idea Assessment Pipeline" in res.output


class TestIntegrationDomain:
    def test_integration_manager_agents(self):
        mgr = IntegrationManager()
        agents = mgr.get_all_agents()
        assert "copilot" in agents
        assert "claude" in agents
        assert "trae" in agents
        assert "qwen" in agents
        assert "cline" in agents
        assert "devin" in agents

        # Alias resolution
        assert mgr.resolve_key("lingma") == "qwen"
        assert mgr.resolve_key("kimi") == "generic"

    def test_integration_cli_commands(self):
        res = runner.invoke(app, ["integration", "list", "--all"])
        assert res.exit_code == 0
        assert "GitHub Copilot" in res.output
        assert "Claude Code" in res.output

        res = runner.invoke(app, ["integration", "info", "claude"])
        assert res.exit_code == 0
        assert ".claude/" in res.output

        res = runner.invoke(app, ["integration", "catalog", "list"])
        assert res.exit_code == 0


class TestArtifactDomain:
    def test_artifact_inspector(self, tmp_path):
        specs_dir = tmp_path / "specs" / "feature-1"
        specs_dir.mkdir(parents=True)
        (specs_dir / "spec.md").write_text(
            "# Feature Spec\nSome details", encoding="utf-8"
        )
        (specs_dir / "tasks.md").write_text(
            "# Tasks\n- [x] Task 1\n- [ ] Task 2\n", encoding="utf-8"
        )

        inspector = ArtifactInspector(project_root=tmp_path)
        items = inspector.list_artifacts()
        assert len(items) == 2
        tasks_item = next(i for i in items if i.artifact_type == "tasks")
        assert tasks_item.tasks_total == 2
        assert tasks_item.tasks_completed == 1

    def test_artifact_cli_commands(self):
        res = runner.invoke(app, ["artifact", "list"])
        assert res.exit_code == 0

        res = runner.invoke(app, ["artifact", "inspect"])
        assert res.exit_code == 0


class TestEventDomain:
    def test_event_dispatcher(self, tmp_path):
        hooks_dir = tmp_path / ".specify" / "hooks"
        hooks_dir.mkdir(parents=True)
        hook_script = hooks_dir / "pre-specify.sh"
        hook_script.write_text("#!/bin/sh\necho 'Hook fired'\n", encoding="utf-8")
        hook_script.chmod(0o755)

        dispatcher = EventDispatcher(project_root=tmp_path)
        hooks = dispatcher.discover_hooks("pre-specify")
        assert len(hooks) == 1
        assert hooks[0].event_name == "pre-specify"

        results = dispatcher.run_event("pre-specify")
        assert len(results) == 1
        assert results[0][1] == 0
        assert "Hook fired" in results[0][2]

    def test_event_cli_commands(self):
        res = runner.invoke(app, ["event", "list"])
        assert res.exit_code == 0


class TestSelfDomain:
    def test_self_cli_commands(self):
        res = runner.invoke(app, ["self", "check"])
        assert res.exit_code == 0

        res = runner.invoke(app, ["self", "upgrade", "--dry-run"])
        assert res.exit_code == 0
        assert "[DRY-RUN]" in res.output
