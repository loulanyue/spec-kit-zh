# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Tests for the `specify doctor` diagnostics helpers."""

from pathlib import Path
from unittest.mock import patch

from specify_cli import _build_doctor_recommendations, _collect_doctor_diagnostics


def test_build_doctor_recommendations_for_uninitialized_project():
    """Doctor should suggest init and core environment fixes when basics are missing."""
    diagnostics = {
        "git_available": False,
        "uv_available": False,
        "has_github_token": False,
        "github_connectivity_ok": False,
        "github_connectivity_detail": "无法连接 GitHub API：timeout",
        "is_spec_project": False,
        "is_git_repo": False,
        "missing_agents": ["claude", "gemini"],
    }

    recommendations = _build_doctor_recommendations(diagnostics)

    assert any("安装 Git" in item for item in recommendations)
    assert any("安装 uv" in item or "uv" in item for item in recommendations)
    assert any("GH_TOKEN" in item or "GITHUB_TOKEN" in item for item in recommendations)
    assert any("specify init --here --ai claude" in item for item in recommendations)
    assert any("claude, gemini" in item for item in recommendations)


def test_build_doctor_recommendations_for_existing_spec_project_without_git():
    """Doctor should point existing projects toward git setup instead of init."""
    diagnostics = {
        "git_available": True,
        "uv_available": True,
        "has_github_token": True,
        "github_connectivity_ok": True,
        "github_connectivity_detail": "GitHub API 可访问",
        "is_spec_project": True,
        "is_git_repo": False,
        "missing_agents": [],
    }

    recommendations = _build_doctor_recommendations(diagnostics)

    assert any("git init" in item for item in recommendations)
    assert not any("specify init --here --ai claude" in item for item in recommendations)


def test_collect_doctor_diagnostics_reads_project_state(tmp_path: Path):
    """Collected diagnostics should reflect the current project directory state."""
    project_dir = tmp_path / "demo"
    (project_dir / ".specify").mkdir(parents=True)

    with patch("specify_cli.check_tool") as mock_check_tool, patch(
        "specify_cli.is_git_repo", return_value=True
    ), patch("specify_cli._check_github_connectivity", return_value=(True, "GitHub API 可访问")), patch(
        "specify_cli._github_token", return_value="token"
    ):
        def fake_check(tool, tracker=None):
            return tool in {"git", "uv", "claude"}

        mock_check_tool.side_effect = fake_check
        diagnostics = _collect_doctor_diagnostics(project_dir)

    assert diagnostics["path"] == project_dir
    assert diagnostics["is_spec_project"] is True
    assert diagnostics["is_git_repo"] is True
    assert diagnostics["git_available"] is True
    assert diagnostics["uv_available"] is True
    assert diagnostics["has_github_token"] is True
    assert diagnostics["github_connectivity_ok"] is True
    assert diagnostics["available_agent_count"] >= 1
    assert "claude" not in diagnostics["missing_agents"]
