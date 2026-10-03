"""Tests for domestic developer experience features: --offline and --mirror."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from specify_cli import (
    app,
    bootstrap_template_from_fallback_source,
    resolve_mirror_url,
)
import specify_cli.templates as templates_mod


def test_resolve_mirror_url_presets():
    gh_url = "https://github.com/github/spec-kit/releases/download/v1.0.13/spec-kit-template-claude-sh.zip"

    # Fastgit preset
    mirrored = resolve_mirror_url(gh_url, "fastgit")
    assert mirrored == f"https://ghfast.top/{gh_url}"

    # ghproxy preset
    mirrored_proxy = resolve_mirror_url(gh_url, "ghproxy")
    assert mirrored_proxy == f"https://ghproxy.net/{gh_url}"

    # cf preset
    mirrored_cf = resolve_mirror_url(gh_url, "cf")
    assert mirrored_cf == f"https://mirror.ghproxy.com/{gh_url}"


def test_resolve_mirror_url_custom_prefix():
    gh_url = "https://github.com/owner/repo/archive.zip"
    custom_prefix = "https://mirror.example.org"
    mirrored = resolve_mirror_url(gh_url, custom_prefix)
    assert mirrored == f"https://mirror.example.org/{gh_url}"


def test_resolve_mirror_url_env_var(monkeypatch):
    gh_url = "https://github.com/owner/repo/archive.zip"
    monkeypatch.setenv("SPECIFY_MIRROR", "fastgit")
    assert resolve_mirror_url(gh_url) == f"https://ghfast.top/{gh_url}"


def test_resolve_mirror_url_idempotent():
    gh_url = "https://ghfast.top/https://github.com/owner/repo/archive.zip"
    assert resolve_mirror_url(gh_url, "fastgit") == gh_url


def test_bootstrap_template_offline_does_not_network_clone(tmp_path: Path, monkeypatch):
    """Offline bootstrap must never call git clone or network requests."""
    fake_asset_root = tmp_path / "bundled"
    (fake_asset_root / "templates").mkdir(parents=True)
    (fake_asset_root / "scripts").mkdir(parents=True)
    (fake_asset_root / "templates" / "spec-template.md").write_text("Spec Template")

    monkeypatch.setattr(
        templates_mod, "_bundled_asset_root_from_package", lambda: fake_asset_root
    )

    def _unexpected_clone(*args, **kwargs):
        raise AssertionError("git clone must not be called in offline mode!")

    monkeypatch.setattr(templates_mod.subprocess, "run", _unexpected_clone)

    project_dir = tmp_path / "offline_project"
    bootstrap_template_from_fallback_source(
        project_dir,
        ai_assistant="claude",
        script_type="sh",
        is_current_dir=False,
        verbose=False,
        offline=True,
    )

    assert (project_dir / ".specify" / "templates" / "spec-template.md").exists()


def test_init_command_with_offline_flag(tmp_path: Path):
    """specify-zh init with --offline must succeed without network calls."""
    runner = CliRunner()
    project_dir = tmp_path / "offline_proj"

    with (
        patch("specify_cli.download_and_extract_template") as mock_extract,
        patch("specify_cli.ensure_executable_scripts"),
        patch("specify_cli.ensure_constitution_from_template"),
        patch("specify_cli.is_git_repo", return_value=False),
        patch("specify_cli.check_tool", return_value=True),
    ):
        result = runner.invoke(
            app,
            ["init", str(project_dir), "--ai", "claude", "--offline", "--no-git"],
        )

        assert result.exit_code == 0
        mock_extract.assert_called_once()
        _, kwargs = mock_extract.call_args
        assert kwargs.get("offline") is True
