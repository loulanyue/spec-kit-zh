# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Smoke tests for specify-cli-zh CLI.

Tests key entry points to prevent packaging/branding regressions.
Run with: pytest tests/test_smoke.py -v
Or via: make smoke
"""

import subprocess
import re
import sys
import tomllib
from pathlib import Path


# Path to project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run specify-zh CLI and return CompletedProcess."""
    return subprocess.run(
        ["specify-zh"] + args,
        capture_output=True,
        text=True,
        **kwargs,
    )


class TestSmokeCLI:
    """Smoke tests for specify-zh CLI entry points."""

    def test_help_exits_zero(self):
        """specify-zh --help should exit with code 0."""
        result = _run(["--help"])
        assert result.returncode == 0, f"Expected 0, got {result.returncode}\n{result.stderr}"

    def test_version_exits_zero(self):
        """specify-zh version should exit with code 0."""
        result = _run(["version"])
        assert result.returncode == 0, f"Expected 0, got {result.returncode}\n{result.stderr}"

    def test_version_contains_version_number(self):
        """specify-zh version should output a semver-like version number."""
        result = _run(["version"])
        output = result.stdout + result.stderr
        assert re.search(r"\d+\.\d+\.\d+", output), (
            f"No version number found in output:\n{output}"
        )

    def test_init_help_exits_zero(self):
        """specify-zh init --help should exit with code 0."""
        result = _run(["init", "--help"])
        assert result.returncode == 0, f"Expected 0, got {result.returncode}\n{result.stderr}"

    def test_init_help_contains_ai_option(self):
        """specify-zh init --help should mention --ai option."""
        result = _run(["init", "--help"])
        output = result.stdout + result.stderr
        assert "--ai" in output, f"--ai not found in help output:\n{output}"

    def test_check_exits_zero(self):
        """specify-zh check should exit with code 0."""
        result = _run(["check"])
        assert result.returncode == 0, f"Expected 0, got {result.returncode}\n{result.stderr}"

    def test_no_old_brand_in_help(self):
        """specify-zh --help should not contain old brand name 'Specify CLI' (without -zh)."""
        result = _run(["--help"])
        output = result.stdout + result.stderr
        # "specify-cli-zh" is OK, standalone "Specify CLI" (without -zh) should not appear
        # Strip occurrences of "specify-cli-zh" before checking
        sanitized = output.replace("specify-cli-zh", "").replace("specify-zh", "")
        assert "Specify CLI" not in sanitized, (
            f"Old brand 'Specify CLI' found in help output:\n{output}"
        )


class TestPyprojectScripts:
    """Tests for pyproject.toml configuration."""

    def test_specify_zh_entry_point_exists(self):
        """pyproject.toml should declare specify-zh as a script entry point."""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        scripts = data.get("project", {}).get("scripts", {})
        assert "specify-zh" in scripts, (
            f"'specify-zh' entry point not found in pyproject.toml [project.scripts].\n"
            f"Current scripts: {scripts}"
        )
