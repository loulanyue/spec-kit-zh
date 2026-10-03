# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""Self upgrade and version checking for specify-cli-zh."""

from __future__ import annotations

import shutil
import subprocess
import sys

import httpx

from specify_cli.network import resolve_mirror_url

PYPI_JSON_URL = "https://pypi.org/pypi/specify-cli-zh/json"
GITHUB_LATEST_URL = "https://api.github.com/repos/loulanyue/spec-kit-zh/releases/latest"


def check_latest_version(mirror: str | None = None) -> tuple[str | None, str | None]:
    """Query PyPI or GitHub API for the latest published version."""
    url = PYPI_JSON_URL
    if mirror:
        url = resolve_mirror_url(url, mirror)

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                version = data.get("info", {}).get("version")
                if version:
                    return version, "PyPI"
    except Exception:
        pass

    # Fallback to GitHub releases
    try:
        gh_url = resolve_mirror_url(GITHUB_LATEST_URL, mirror)
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(gh_url, headers={"User-Agent": "specify-cli-zh"})
            if resp.status_code == 200:
                data = resp.json()
                tag = str(data.get("tag_name", "")).lstrip("v")
                if tag:
                    return tag, "GitHub"
    except Exception:
        pass

    return None, None


def upgrade_in_place(
    package_name: str = "specify-cli-zh",
    dry_run: bool = False,
    mirror: str | None = None,
) -> tuple[bool, str]:
    """Execute uv or pip to upgrade specify-cli-zh."""
    has_uv = shutil.which("uv") is not None
    cmd: list[str] = []

    if has_uv:
        cmd = ["uv", "tool", "upgrade", package_name]
    else:
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package_name]

    if mirror:
        # e.g., if PyPI mirror is provided or proxy
        if "tsinghua" in mirror or "aliyun" in mirror:
            cmd.extend(["-i", mirror])

    if dry_run:
        return True, f"[DRY-RUN] 将会执行命令: {' '.join(cmd)}"

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, res.stdout
    except subprocess.CalledProcessError as e:
        return False, f"升级失败 (退出码 {e.returncode}):\n{e.stderr or e.stdout}"
    except Exception as exc:
        return False, f"执行异常: {exc}"
