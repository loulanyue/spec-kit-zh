# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
import ssl
import sys
import types
from pathlib import Path

import httpx
import pytest

if "readchar" not in sys.modules:
    sys.modules["readchar"] = types.SimpleNamespace()

if "truststore" not in sys.modules:
    sys.modules["truststore"] = types.SimpleNamespace(SSLContext=ssl.SSLContext)

import specify_cli


def _make_fake_asset_root(root: Path) -> Path:
    (root / "templates" / "commands").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / "bash").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / "powershell").mkdir(parents=True, exist_ok=True)

    (root / "templates" / "spec-template.md").write_text("# spec\n", encoding="utf-8")
    (root / "templates" / "plan-template.md").write_text("# plan\n", encoding="utf-8")
    (root / "templates" / "tasks-template.md").write_text("# tasks\n", encoding="utf-8")
    (root / "templates" / "constitution-template.md").write_text("# constitution\n", encoding="utf-8")
    (root / "templates" / "checklist-template.md").write_text("# checklist\n", encoding="utf-8")
    (root / "templates" / "agent-file-template.md").write_text("# agent\n", encoding="utf-8")
    (root / "templates" / "vscode-settings.json").write_text("{}", encoding="utf-8")
    (root / "templates" / "commands" / "specify.md").write_text(
        "---\n"
        "description: test\n"
        "---\n\n"
        "run $ARGUMENTS\n",
        encoding="utf-8",
    )
    (root / "scripts" / "bash" / "common.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (root / "scripts" / "powershell" / "common.ps1").write_text("# powershell\n", encoding="utf-8")
    return root


def test_bootstrap_template_prefers_packaged_assets(tmp_path, monkeypatch):
    asset_root = _make_fake_asset_root(tmp_path / "bundled")
    project_path = tmp_path / "project"

    monkeypatch.setattr(specify_cli, "_bundled_asset_root_from_package", lambda: asset_root)

    def _unexpected_clone(*args, **kwargs):
        raise AssertionError("git clone should not run when bundled assets are available")

    monkeypatch.setattr(specify_cli.subprocess, "run", _unexpected_clone)

    specify_cli.bootstrap_template_from_fallback_source(
        project_path,
        ai_assistant="claude",
        script_type="sh",
        is_current_dir=False,
        verbose=False,
    )

    assert (project_path / ".specify" / "templates" / "spec-template.md").exists()
    assert (project_path / ".specify" / "scripts" / "bash" / "common.sh").exists()
    assert (project_path / ".claude" / "commands" / "speckit.specify.md").exists()


def test_download_template_from_github_raises_runtime_error_on_rate_limit(tmp_path):
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                403,
                headers={
                    "X-RateLimit-Limit": "60",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": "1775222462",
                },
                text="rate limited",
            )
        )
    )

    with pytest.raises(RuntimeError) as exc:
        specify_cli.download_template_from_github(
            "claude",
            tmp_path,
            client=client,
            verbose=False,
            show_progress=False,
        )

    assert "GitHub API returned status 403" in str(exc.value)
