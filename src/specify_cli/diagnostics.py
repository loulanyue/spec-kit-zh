"""Doctor command diagnostic routines and health checks for specify-cli-zh."""

from __future__ import annotations

import shutil
import sys
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

from specify_cli.agents import AGENT_CONFIG
from specify_cli.constants import CMD_NAME, DIST_NAME
from specify_cli.git import _doctor_install_hint, check_tool, is_git_repo
from specify_cli.network import (
    _github_auth_headers,
    _github_token,
    _parse_rate_limit_headers,
    client,
)


def _resolve(name: str, fallback: Any) -> Any:
    """Resolve symbol from sys.modules['specify_cli'] if available (supports unittest.mock.patch)."""
    pkg = sys.modules.get("specify_cli")
    if pkg is not None and hasattr(pkg, name):
        return getattr(pkg, name)
    return fallback


def _check_github_connectivity(timeout: float = 5.0) -> tuple[bool, str]:
    """Check whether GitHub API is reachable and return a short status detail."""
    http_client = _resolve("client", client)
    auth_headers_fn = _resolve("_github_auth_headers", _github_auth_headers)
    parse_headers_fn = _resolve("_parse_rate_limit_headers", _parse_rate_limit_headers)

    url = "https://api.github.com/rate_limit"
    try:
        response = http_client.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers=auth_headers_fn(),
        )
        if response.status_code == 200:
            return True, "GitHub API 可访问"
        if response.status_code in (401, 403):
            info = parse_headers_fn(response.headers)
            if "remaining" in info and info.get("remaining") == "0":
                return False, "GitHub API 已触发限流，建议配置 GH_TOKEN"
            return False, f"GitHub API 返回 {response.status_code}"
        return False, f"GitHub API 返回 {response.status_code}"
    except Exception as exc:
        return False, f"无法连接 GitHub API：{exc}"


def _collect_doctor_diagnostics(project_path: Path | None = None) -> dict:
    """Collect environment and project diagnostics for the doctor command."""
    github_token_fn = _resolve("_github_token", _github_token)
    check_tool_fn = _resolve("check_tool", check_tool)
    is_git_repo_fn = _resolve("is_git_repo", is_git_repo)
    conn_check_fn = _resolve("_check_github_connectivity", _check_github_connectivity)
    shutil_mod = _resolve("shutil", shutil)

    current_path = project_path or Path.cwd()
    spec_dir = current_path / ".specify"
    has_github_token = bool(github_token_fn())

    required_agent_cli = {}
    for agent_key, agent_config in AGENT_CONFIG.items():
        if agent_key == "generic" or not agent_config.get("requires_cli"):
            continue
        required_agent_cli[agent_key] = check_tool_fn(agent_key)

    github_ok, github_detail = conn_check_fn()

    dist_ok = False
    try:
        importlib_metadata.version(DIST_NAME)
        dist_ok = True
    except Exception:
        pass

    cmd_path = shutil_mod.which(CMD_NAME)

    return {
        "path": current_path,
        "python_version": sys.version.split()[0],
        "git_available": check_tool_fn("git"),
        "uv_available": check_tool_fn("uv"),
        "has_github_token": has_github_token,
        "github_connectivity_ok": github_ok,
        "github_connectivity_detail": github_detail,
        "is_git_repo": is_git_repo_fn(current_path),
        "is_spec_project": spec_dir.exists(),
        "required_agent_cli": required_agent_cli,
        "available_agent_count": sum(1 for ok in required_agent_cli.values() if ok),
        "missing_agents": sorted(
            [agent for agent, ok in required_agent_cli.items() if not ok]
        ),
        "dist_ok": dist_ok,
        "cmd_path": cmd_path,
    }


def _build_doctor_recommendations(diagnostics: dict) -> list[str]:
    """Build actionable recommendations from doctor diagnostics."""
    hint_fn = _resolve("_doctor_install_hint", _doctor_install_hint)
    recommendations: list[str] = []

    if not diagnostics["git_available"]:
        recommendations.append(hint_fn("git"))

    if not diagnostics["uv_available"]:
        recommendations.append(hint_fn("uv"))

    if not diagnostics["has_github_token"]:
        recommendations.append(
            "建议配置 `GH_TOKEN` 或 `GITHUB_TOKEN`，可显著提升 GitHub API 限流阈值。\n"
            "   [dim]执行命令：export GITHUB_TOKEN=ghp_xxxxx （或配置 gh auth login）[/dim]"
        )

    if not diagnostics["github_connectivity_ok"]:
        recommendations.append(
            f"{diagnostics['github_connectivity_detail']}。若在受限网络环境中，请稍后重试、配置代理，或改用离线模板包。\n"
            "   [dim]离线方案：手动下载模板仓库到本地，使用 specify-zh init --template-dir <本地路径>[/dim]"
        )

    if not diagnostics["is_spec_project"]:
        recommendations.append(
            "当前目录尚未初始化为 spec-kit 项目。可运行 `specify-zh init --here --ai claude` 开始。"
        )
    elif not diagnostics["is_git_repo"]:
        recommendations.append(
            "当前目录已包含 `.specify/`，但还不是 Git 仓库。建议运行 `git init` 并提交初始模板。"
        )

    if diagnostics["missing_agents"]:
        preview = ", ".join(diagnostics["missing_agents"][:3])
        if len(diagnostics["missing_agents"]) > 3:
            preview += " 等"
        recommendations.append(
            f"当前缺少可直接调用的 AI CLI：{preview}。如需最佳体验，请至少安装一个常用 agent。"
        )

    if not recommendations:
        recommendations.append(
            "当前环境状态良好，可以直接开始使用 `specify-zh init` 或项目内 slash commands。"
        )

    return recommendations


__all__ = [
    "_build_doctor_recommendations",
    "_check_github_connectivity",
    "_collect_doctor_diagnostics",
]
