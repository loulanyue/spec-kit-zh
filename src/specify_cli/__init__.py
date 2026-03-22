#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "platformdirs",
#     "readchar",
#     "httpx",
# ]
# ///
"""
specify-cli-zh - 规范驱动开发项目设置工具

Usage:
    uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify-zh init <project-name>
    uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify-zh init .
    uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify-zh init --here

Or install globally:
    uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git
    specify-zh init <project-name>
    specify-zh init .
    specify-zh init --here
"""

import os
import re
import subprocess
import sys
import zipfile
import tempfile
import shutil
import shlex
import json
import yaml
from pathlib import Path
from typing import Optional, Tuple

import typer
from specify_cli.constants import DIST_NAME, CMD_NAME, BRAND_DISPLAY, UPSTREAM_REPO, TAGLINE
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.table import Table
from rich.tree import Tree
from typer.core import TyperGroup

# For cross-platform keyboard input
import readchar
import ssl
import truststore
from datetime import datetime, timezone

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    tomllib = None

ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
client = httpx.Client(verify=ssl_context)

def _github_token(cli_token: str | None = None) -> str | None:
    """Return sanitized GitHub token (cli arg takes precedence) or None."""
    return ((cli_token or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or "").strip()) or None

def _github_auth_headers(cli_token: str | None = None) -> dict:
    """Return Authorization header dict only when a non-empty token exists."""
    token = _github_token(cli_token)
    return {"Authorization": f"Bearer {token}"} if token else {}

def _parse_rate_limit_headers(headers: httpx.Headers) -> dict:
    """Extract and parse GitHub rate-limit headers."""
    info = {}
    
    # Standard GitHub rate-limit headers
    if "X-RateLimit-Limit" in headers:
        info["limit"] = headers.get("X-RateLimit-Limit")
    if "X-RateLimit-Remaining" in headers:
        info["remaining"] = headers.get("X-RateLimit-Remaining")
    if "X-RateLimit-Reset" in headers:
        reset_epoch = int(headers.get("X-RateLimit-Reset", "0"))
        if reset_epoch:
            reset_time = datetime.fromtimestamp(reset_epoch, tz=timezone.utc)
            info["reset_epoch"] = reset_epoch
            info["reset_time"] = reset_time
            info["reset_local"] = reset_time.astimezone()
    
    # Retry-After header (seconds or HTTP-date)
    if "Retry-After" in headers:
        retry_after = headers.get("Retry-After")
        try:
            info["retry_after_seconds"] = int(retry_after)
        except ValueError:
            # HTTP-date format - not implemented, just store as string
            info["retry_after"] = retry_after
    
    return info

def _format_rate_limit_error(status_code: int, headers: httpx.Headers, url: str) -> str:
    """Format a user-friendly error message with rate-limit information."""
    rate_info = _parse_rate_limit_headers(headers)
    
    lines = [f"GitHub API returned status {status_code} for {url}"]
    lines.append("")
    
    if rate_info:
        lines.append("[bold]Rate Limit Information:[/bold]")
        if "limit" in rate_info:
            lines.append(f"  • Rate Limit: {rate_info['limit']} requests/hour")
        if "remaining" in rate_info:
            lines.append(f"  • Remaining: {rate_info['remaining']}")
        if "reset_local" in rate_info:
            reset_str = rate_info["reset_local"].strftime("%Y-%m-%d %H:%M:%S %Z")
            lines.append(f"  • Resets at: {reset_str}")
        if "retry_after_seconds" in rate_info:
            lines.append(f"  • Retry after: {rate_info['retry_after_seconds']} seconds")
        lines.append("")
    
    # Add troubleshooting guidance
    lines.append("[bold]Troubleshooting Tips:[/bold]")
    lines.append("  • If you're on a shared CI or corporate environment, you may be rate-limited.")
    lines.append("  • Consider using a GitHub token via --github-token or the GH_TOKEN/GITHUB_TOKEN")
    lines.append("    environment variable to increase rate limits.")
    lines.append("  • Authenticated requests have a limit of 5,000/hour vs 60/hour for unauthenticated.")
    
    return "\n".join(lines)

# Agent configuration with name, folder, install URL, CLI tool requirement, and commands subdirectory
AGENT_CONFIG = {
    "copilot": {
        "name": "GitHub Copilot",
        "folder": ".github/",
        "commands_subdir": "agents",  # Special: uses agents/ not commands/
        "install_url": None,  # IDE-based, no CLI check needed
        "requires_cli": False,
    },
    "claude": {
        "name": "Claude Code",
        "folder": ".claude/",
        "commands_subdir": "commands",
        "install_url": "https://docs.anthropic.com/en/docs/claude-code/setup",
        "requires_cli": True,
    },
    "gemini": {
        "name": "Gemini CLI",
        "folder": ".gemini/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/google-gemini/gemini-cli",
        "requires_cli": True,
    },
    "cursor-agent": {
        "name": "Cursor",
        "folder": ".cursor/",
        "commands_subdir": "commands",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "qwen": {
        "name": "Qwen Code",
        "folder": ".qwen/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/QwenLM/qwen-code",
        "requires_cli": True,
    },
    "opencode": {
        "name": "opencode",
        "folder": ".opencode/",
        "commands_subdir": "command",  # Special: singular 'command' not 'commands'
        "install_url": "https://opencode.ai",
        "requires_cli": True,
    },
    "codex": {
        "name": "Codex CLI",
        "folder": ".codex/",
        "commands_subdir": "prompts",  # Special: uses prompts/ not commands/
        "install_url": "https://github.com/openai/codex",
        "requires_cli": True,
    },
    "windsurf": {
        "name": "Windsurf",
        "folder": ".windsurf/",
        "commands_subdir": "workflows",  # Special: uses workflows/ not commands/
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "kilocode": {
        "name": "Kilo Code",
        "folder": ".kilocode/",
        "commands_subdir": "workflows",  # Special: uses workflows/ not commands/
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "auggie": {
        "name": "Auggie CLI",
        "folder": ".augment/",
        "commands_subdir": "commands",
        "install_url": "https://docs.augmentcode.com/cli/setup-auggie/install-auggie-cli",
        "requires_cli": True,
    },
    "codebuddy": {
        "name": "CodeBuddy",
        "folder": ".codebuddy/",
        "commands_subdir": "commands",
        "install_url": "https://www.codebuddy.ai/cli",
        "requires_cli": True,
    },
    "qodercli": {
        "name": "Qoder CLI",
        "folder": ".qoder/",
        "commands_subdir": "commands",
        "install_url": "https://qoder.com/cli",
        "requires_cli": True,
    },
    "roo": {
        "name": "Roo Code",
        "folder": ".roo/",
        "commands_subdir": "commands",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "kiro-cli": {
        "name": "Kiro CLI",
        "folder": ".kiro/",
        "commands_subdir": "prompts",  # Special: uses prompts/ not commands/
        "install_url": "https://kiro.dev/docs/cli/",
        "requires_cli": True,
    },
    "amp": {
        "name": "Amp",
        "folder": ".agents/",
        "commands_subdir": "commands",
        "install_url": "https://ampcode.com/manual#install",
        "requires_cli": True,
    },
    "shai": {
        "name": "SHAI",
        "folder": ".shai/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/ovh/shai",
        "requires_cli": True,
    },
    "tabnine": {
        "name": "Tabnine CLI",
        "folder": ".tabnine/agent/",
        "commands_subdir": "commands",
        "install_url": "https://docs.tabnine.com/main/getting-started/tabnine-cli",
        "requires_cli": True,
    },
    "agy": {
        "name": "Antigravity",
        "folder": ".agent/",
        "commands_subdir": "workflows",  # Special: uses workflows/ not commands/
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "bob": {
        "name": "IBM Bob",
        "folder": ".bob/",
        "commands_subdir": "commands",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "vibe": {
        "name": "Mistral Vibe",
        "folder": ".vibe/",
        "commands_subdir": "prompts",
        "install_url": "https://github.com/mistralai/mistral-vibe",
        "requires_cli": True,
    },
    "generic": {
        "name": "Generic (bring your own agent)",
        "folder": None,  # Set dynamically via --ai-commands-dir
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    },
}

AI_ASSISTANT_ALIASES = {
    "kiro": "kiro-cli",
}

def _build_ai_assistant_help() -> str:
    """根据 AGENT_CONFIG 动态构建 --ai 帮助文本，避免与运行时配置脱节。"""

    non_generic_agents = sorted(agent for agent in AGENT_CONFIG if agent != "generic")
    base_help = (
        f"可选 AI 助手: {', '.join(non_generic_agents)}, "
        "或 generic（需搭配 --ai-commands-dir）。"
    )

    if not AI_ASSISTANT_ALIASES:
        return base_help

    alias_phrases = []
    for alias, target in sorted(AI_ASSISTANT_ALIASES.items()):
        alias_phrases.append(f"将 '{alias}' 作为 '{target}' 的别名")

    if len(alias_phrases) == 1:
        aliases_text = alias_phrases[0]
    else:
        aliases_text = ', '.join(alias_phrases[:-1]) + ' and ' + alias_phrases[-1]

    return base_help + " 可使用 " + aliases_text + "。"
AI_ASSISTANT_HELP = _build_ai_assistant_help()

SCRIPT_TYPE_CHOICES = {"sh": "POSIX Shell (bash/zsh)", "ps": "PowerShell"}

CLAUDE_LOCAL_PATH = Path.home() / ".claude" / "local" / "claude"

BANNER = """
███████╗██████╗ ███████╗ ██████╗██╗███████╗██╗   ██╗
██╔════╝██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝
███████╗██████╔╝█████╗  ██║     ██║█████╗   ╚████╔╝ 
╚════██║██╔═══╝ ██╔══╝  ██║     ██║██╔══╝    ╚██╔╝  
███████║██║     ███████╗╚██████╗██║██║        ██║   
╚══════╝╚═╝     ╚══════╝ ╚═════╝╚═╝╚═╝        ╚═╝   
"""

TAGLINE = TAGLINE
class StepTracker:
    """Track and render hierarchical steps without emojis, similar to Claude Code tree output.
    Supports live auto-refresh via an attached refresh callback.
    """
    def __init__(self, title: str):
        self.title = title
        self.steps = []  # list of dicts: {key, label, status, detail}
        self.status_order = {"pending": 0, "running": 1, "done": 2, "error": 3, "skipped": 4}
        self._refresh_cb = None  # callable to trigger UI refresh

    def attach_refresh(self, cb):
        self._refresh_cb = cb

    def add(self, key: str, label: str):
        if key not in [s["key"] for s in self.steps]:
            self.steps.append({"key": key, "label": label, "status": "pending", "detail": ""})
            self._maybe_refresh()

    def start(self, key: str, detail: str = ""):
        self._update(key, status="running", detail=detail)

    def complete(self, key: str, detail: str = ""):
        self._update(key, status="done", detail=detail)

    def error(self, key: str, detail: str = ""):
        self._update(key, status="error", detail=detail)

    def skip(self, key: str, detail: str = ""):
        self._update(key, status="skipped", detail=detail)

    def _update(self, key: str, status: str, detail: str):
        for s in self.steps:
            if s["key"] == key:
                s["status"] = status
                if detail:
                    s["detail"] = detail
                self._maybe_refresh()
                return

        self.steps.append({"key": key, "label": key, "status": status, "detail": detail})
        self._maybe_refresh()

    def _maybe_refresh(self):
        if self._refresh_cb:
            try:
                self._refresh_cb()
            except Exception:
                pass

    def render(self):
        tree = Tree(f"[cyan]{self.title}[/cyan]", guide_style="grey50")
        for step in self.steps:
            label = step["label"]
            detail_text = step["detail"].strip() if step["detail"] else ""

            status = step["status"]
            if status == "done":
                symbol = "[green]●[/green]"
            elif status == "pending":
                symbol = "[green dim]○[/green dim]"
            elif status == "running":
                symbol = "[cyan]○[/cyan]"
            elif status == "error":
                symbol = "[red]●[/red]"
            elif status == "skipped":
                symbol = "[yellow]○[/yellow]"
            else:
                symbol = " "

            if status == "pending":
                # Entire line light gray (pending)
                if detail_text:
                    line = f"{symbol} [bright_black]{label} ({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [bright_black]{label}[/bright_black]"
            else:
                # Label white, detail (if any) light gray in parentheses
                if detail_text:
                    line = f"{symbol} [white]{label}[/white] [bright_black]({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [white]{label}[/white]"

            tree.add(line)
        return tree

def get_key():
    """Get a single keypress in a cross-platform way using readchar."""
    key = readchar.readkey()

    if key == readchar.key.UP or key == readchar.key.CTRL_P:
        return 'up'
    if key == readchar.key.DOWN or key == readchar.key.CTRL_N:
        return 'down'

    if key == readchar.key.ENTER:
        return 'enter'

    if key == readchar.key.ESC:
        return 'escape'

    if key == readchar.key.CTRL_C:
        raise KeyboardInterrupt

    return key

def select_with_arrows(options: dict, prompt_text: str = "选择一个选项", default_key: str = None) -> str:
    """
    Interactive selection using arrow keys with Rich Live display.
    
    Args:
        options: Dict with keys as option keys and values as descriptions
        prompt_text: Text to show above the options
        default_key: Default option key to start with
        
    Returns:
        Selected option key
    """
    option_keys = list(options.keys())
    if default_key and default_key in option_keys:
        selected_index = option_keys.index(default_key)
    else:
        selected_index = 0

    selected_key = None

    def create_selection_panel():
        """Create the selection panel with current selection highlighted."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="left", width=3)
        table.add_column(style="white", justify="left")

        for i, key in enumerate(option_keys):
            if i == selected_index:
                table.add_row("▶", f"[cyan]{key}[/cyan] [dim]({options[key]})[/dim]")
            else:
                table.add_row(" ", f"[cyan]{key}[/cyan] [dim]({options[key]})[/dim]")

        table.add_row("", "")
        table.add_row("", "[dim]使用 ↑/↓ 导航，Enter 确认，Esc 取消[/dim]")

        return Panel(
            table,
            title=f"[bold]{prompt_text}[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )

    console.print()

    def run_selection_loop():
        nonlocal selected_key, selected_index
        with Live(create_selection_panel(), console=console, transient=True, auto_refresh=False) as live:
            while True:
                try:
                    key = get_key()
                    if key == 'up':
                        selected_index = (selected_index - 1) % len(option_keys)
                    elif key == 'down':
                        selected_index = (selected_index + 1) % len(option_keys)
                    elif key == 'enter':
                        selected_key = option_keys[selected_index]
                        break
                    elif key == 'escape':
                        console.print("\n[yellow]已取消选择[/yellow]")
                        raise typer.Exit(1)

                    live.update(create_selection_panel(), refresh=True)

                except KeyboardInterrupt:
                    console.print("\n[yellow]已取消选择[/yellow]")
                    raise typer.Exit(1)

    run_selection_loop()

    if selected_key is None:
        console.print("\n[red]选择失败。[/red]")
        raise typer.Exit(1)

    return selected_key

console = Console()

class BannerGroup(TyperGroup):
    """Custom group that shows banner before help."""

    def format_help(self, ctx, formatter):
        # Show banner before help
        show_banner()
        super().format_help(ctx, formatter)


app = typer.Typer(
    name=CMD_NAME,
    help="specify-cli-zh 规范驱动开发项目设置工具",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)

def show_banner():
    """Display the ASCII art banner."""
    banner_lines = BANNER.strip().split('\n')
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]

    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)

    console.print(Align.center(styled_banner))
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()


def _get_cli_distribution_version() -> tuple[str, str]:
    """Resolve installed CLI version and run mode.

    Returns:
        A (version, source) tuple where source is 'installed' or 'local'.
    """
    import importlib.metadata

    for package_name in (DIST_NAME, "specify-cli"):
        try:
            return importlib.metadata.version(package_name), "installed"
        except Exception:
            continue

    try:
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                ver = data.get("project", {}).get("version", "unknown")
                return ver, "local"
    except Exception:
        pass

    return "unknown", "unknown"

@app.callback()
def callback(ctx: typer.Context):
    """Show banner when no subcommand is provided."""
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        show_banner()
        console.print(Align.center("[dim]运行 'specify-zh --help' 查看使用说明[/dim]"))
        console.print()

def run_command(cmd: list[str], check_return: bool = True, capture: bool = False, shell: bool = False) -> Optional[str]:
    """Run a shell command and optionally capture output."""
    try:
        if capture:
            result = subprocess.run(cmd, check=check_return, capture_output=True, text=True, shell=shell)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=check_return, shell=shell)
            return None
    except subprocess.CalledProcessError as e:
        if check_return:
            console.print(f"[red]执行命令出错：[/red] {' '.join(cmd)}")
            console.print(f"[red]退出码：[/red] {e.returncode}")
            if hasattr(e, 'stderr') and e.stderr:
                console.print(f"[red]错误输出：[/red] {e.stderr}")
            raise
        return None

def check_tool(tool: str, tracker: StepTracker = None) -> bool:
    """Check if a tool is installed. Optionally update tracker.
    
    Args:
        tool: Name of the tool to check
        tracker: Optional StepTracker to update with results
        
    Returns:
        True if tool is found, False otherwise
    """
    # Special handling for Claude CLI after `claude migrate-installer`
    # See: https://github.com/loulanyue/spec-kit-zh/issues/123
    # The migrate-installer command REMOVES the original executable from PATH
    # and creates an alias at ~/.claude/local/claude instead
    # This path should be prioritized over other claude executables in PATH
    if tool == "claude":
        if CLAUDE_LOCAL_PATH.exists() and CLAUDE_LOCAL_PATH.is_file():
            if tracker:
                tracker.complete(tool, "已安装")
            return True
    
    if tool == "kiro-cli":
        # Kiro currently supports both executable names. Prefer kiro-cli and
        # accept kiro as a compatibility fallback.
        found = shutil.which("kiro-cli") is not None or shutil.which("kiro") is not None
    else:
        found = shutil.which(tool) is not None
    
    if tracker:
        if found:
            tracker.complete(tool, "已安装")
        else:
            tracker.error(tool, "未安装")
    
    return found

def is_git_repo(path: Path = None) -> bool:
    """Check if the specified path is inside a git repository."""
    if path is None:
        path = Path.cwd()
    
    if not path.is_dir():
        return False

    try:
        # Use git command to check if inside a work tree
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
            cwd=path,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _doctor_install_hint(tool: str) -> str:
    """Return a short install hint for a missing tool."""
    fixed_hints = {
        "git": "请先安装 Git，然后重新运行 `specify-zh doctor` 或 `specify-zh check`。",
        "uv": "建议安装 uv：`pip install uv`，或参考 https://docs.astral.sh/uv/ 。",
        "code": "如需使用 VS Code，可安装 Visual Studio Code 后重试。",
        "code-insiders": "如需使用 VS Code Insiders，可安装后重试。",
    }
    if tool in fixed_hints:
        return fixed_hints[tool]

    agent_config = AGENT_CONFIG.get(tool)
    if not agent_config:
        return f"请安装 `{tool}` 后重试。"

    install_url = agent_config.get("install_url")
    if install_url:
        return f"请安装 {agent_config['name']} CLI：{install_url}"

    return f"{agent_config['name']} 为 IDE 型 agent，无需单独 CLI。"


def _check_github_connectivity(timeout: float = 5.0) -> tuple[bool, str]:
    """Check whether GitHub API is reachable and return a short status detail."""
    url = "https://api.github.com/rate_limit"
    try:
        response = client.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers=_github_auth_headers(),
        )
        if response.status_code == 200:
            return True, "GitHub API 可访问"
        if response.status_code in (401, 403):
            info = _parse_rate_limit_headers(response.headers)
            if "remaining" in info and info.get("remaining") == "0":
                return False, "GitHub API 已触发限流，建议配置 GH_TOKEN"
            return False, f"GitHub API 返回 {response.status_code}"
        return False, f"GitHub API 返回 {response.status_code}"
    except Exception as exc:
        return False, f"无法连接 GitHub API：{exc}"


def _collect_doctor_diagnostics(project_path: Path | None = None) -> dict:
    """Collect environment and project diagnostics for the doctor command."""
    import shutil
    import importlib.metadata

    current_path = project_path or Path.cwd()
    spec_dir = current_path / ".specify"
    has_github_token = bool(_github_token())

    required_agent_cli = {}
    for agent_key, agent_config in AGENT_CONFIG.items():
        if agent_key == "generic" or not agent_config.get("requires_cli"):
            continue
        required_agent_cli[agent_key] = check_tool(agent_key)

    github_ok, github_detail = _check_github_connectivity()

    dist_ok = False
    try:
        importlib.metadata.version(DIST_NAME)
        dist_ok = True
    except Exception:
        pass
        
    cmd_path = shutil.which(CMD_NAME)

    return {
        "path": current_path,
        "python_version": sys.version.split()[0],
        "git_available": check_tool("git"),
        "uv_available": check_tool("uv"),
        "has_github_token": has_github_token,
        "github_connectivity_ok": github_ok,
        "github_connectivity_detail": github_detail,
        "is_git_repo": is_git_repo(current_path),
        "is_spec_project": spec_dir.exists(),
        "required_agent_cli": required_agent_cli,
        "available_agent_count": sum(1 for ok in required_agent_cli.values() if ok),
        "missing_agents": sorted([agent for agent, ok in required_agent_cli.items() if not ok]),
        "dist_ok": dist_ok,
        "cmd_path": cmd_path,
    }


def _build_doctor_recommendations(diagnostics: dict) -> list[str]:
    """Build actionable recommendations from doctor diagnostics."""
    recommendations: list[str] = []

    if not diagnostics["git_available"]:
        recommendations.append(_doctor_install_hint("git"))

    if not diagnostics["uv_available"]:
        recommendations.append(_doctor_install_hint("uv"))

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
        recommendations.append("当前环境状态良好，可以直接开始使用 `specify-zh init` 或项目内 slash commands。")

    return recommendations

def init_git_repo(project_path: Path, quiet: bool = False) -> Tuple[bool, Optional[str]]:
    """Initialize a git repository in the specified path.
    
    Args:
        project_path: Path to initialize git repository in
        quiet: if True suppress console output (tracker handles status)
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        original_cwd = Path.cwd()
        os.chdir(project_path)
        if not quiet:
            console.print("[cyan]正在初始化 git 仓库...[/cyan]")
        subprocess.run(["git", "init"], check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "Initial commit from Specify template"], check=True, capture_output=True, text=True)
        if not quiet:
            console.print("[green]✓[/green] Git 仓库初始化完成")
        return True, None

    except subprocess.CalledProcessError as e:
        error_msg = f"Command: {' '.join(e.cmd)}\nExit code: {e.returncode}"
        if e.stderr:
            error_msg += f"\nError: {e.stderr.strip()}"
        elif e.stdout:
            error_msg += f"\nOutput: {e.stdout.strip()}"
        
        if not quiet:
            console.print(f"[red]初始化 Git 仓库出错：[/red] {e}")
        return False, error_msg
    finally:
        os.chdir(original_cwd)

def handle_vscode_settings(sub_item, dest_file, rel_path, verbose=False, tracker=None) -> None:
    """Handle merging or copying of .vscode/settings.json files."""
    def log(message, color="green"):
        if verbose and not tracker:
            console.print(f"[{color}]{message}[/] {rel_path}")

    try:
        with open(sub_item, 'r', encoding='utf-8') as f:
            new_settings = json.load(f)

        if dest_file.exists():
            merged = merge_json_files(dest_file, new_settings, verbose=verbose and not tracker)
            with open(dest_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, indent=4)
                f.write('\n')
            log("Merged:", "green")
        else:
            shutil.copy2(sub_item, dest_file)
            log("已复制（原先不存在 settings.json）:", "blue")

    except Exception as e:
        log(f"警告：无法合并，改为直接复制：{e}", "yellow")
        shutil.copy2(sub_item, dest_file)

def merge_json_files(existing_path: Path, new_content: dict, verbose: bool = False) -> dict:
    """Merge new JSON content into existing JSON file.

    Performs a deep merge where:
    - New keys are added
    - Existing keys are preserved unless overwritten by new content
    - Nested dictionaries are merged recursively
    - Lists and other values are replaced (not merged)

    Args:
        existing_path: Path to existing JSON file
        new_content: New JSON content to merge in
        verbose: Whether to print merge details

    Returns:
        Merged JSON content as dict
    """
    try:
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing_content = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is invalid, just use new content
        return new_content

    def deep_merge(base: dict, update: dict) -> dict:
        """Recursively merge update dict into base dict."""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = deep_merge(result[key], value)
            else:
                # Add new key or replace existing value
                result[key] = value
        return result

    merged = deep_merge(existing_content, new_content)

    if verbose:
        console.print(f"[cyan]已合并 JSON 文件：[/cyan] {existing_path.name}")

    return merged

def download_template_from_github(ai_assistant: str, download_dir: Path, *, script_type: str = "sh", verbose: bool = True, show_progress: bool = True, client: httpx.Client = None, debug: bool = False, github_token: str = None) -> Tuple[Path, dict]:
    repo_owner = "github"
    repo_name = "spec-kit"
    if client is None:
        client = httpx.Client(verify=ssl_context)

    if verbose:
        console.print("[cyan]正在获取最新发布信息...[/cyan]")
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    try:
        response = client.get(
            api_url,
            timeout=30,
            follow_redirects=True,
            headers=_github_auth_headers(github_token),
        )
        status = response.status_code
        if status != 200:
            # Format detailed error message with rate-limit info
            error_msg = _format_rate_limit_error(status, response.headers, api_url)
            if debug:
                error_msg += f"\n\n[dim]Response body (truncated 500):[/dim]\n{response.text[:500]}"
            raise RuntimeError(error_msg)
        try:
            release_data = response.json()
        except ValueError as je:
            raise RuntimeError(f"Failed to parse release JSON: {je}\nRaw (truncated 400): {response.text[:400]}")
    except Exception as e:
        console.print("[red]获取发布信息失败[/red]")
        console.print(Panel(str(e), title="获取失败", border_style="red"))
        raise typer.Exit(1)

    assets = release_data.get("assets", [])
    pattern = f"spec-kit-template-{ai_assistant}-{script_type}"
    matching_assets = [
        asset for asset in assets
        if pattern in asset["name"] and asset["name"].endswith(".zip")
    ]

    asset = matching_assets[0] if matching_assets else None

    if asset is None:
        console.print(f"[red]未找到匹配的发布资产[/red]：[bold]{ai_assistant}[/bold]（期望模式：[bold]{pattern}[/bold]）")
        asset_names = [a.get('name', '?') for a in assets]
        console.print(Panel("\n".join(asset_names) or "（无资产）", title="可用资产", border_style="yellow"))
        raise typer.Exit(1)

    download_url = asset["browser_download_url"]
    filename = asset["name"]
    file_size = asset["size"]

    if verbose:
        console.print(f"[cyan]已找到模板：[/cyan] {filename}")
        console.print(f"[cyan]大小：[/cyan] {file_size:,} 字节")
        console.print(f"[cyan]发布版本：[/cyan] {release_data['tag_name']}")

    zip_path = download_dir / filename
    if verbose:
        console.print("[cyan]正在下载模板...[/cyan]")

    try:
        with client.stream(
            "GET",
            download_url,
            timeout=60,
            follow_redirects=True,
            headers=_github_auth_headers(github_token),
        ) as response:
            if response.status_code != 200:
                # Handle rate-limiting on download as well
                error_msg = _format_rate_limit_error(response.status_code, response.headers, download_url)
                if debug:
                    error_msg += f"\n\n[dim]Response body (truncated 400):[/dim]\n{response.text[:400]}"
                raise RuntimeError(error_msg)
            total_size = int(response.headers.get('content-length', 0))
            with open(zip_path, 'wb') as f:
                if total_size == 0:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                else:
                    if show_progress:
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                            console=console,
                        ) as progress:
                            task = progress.add_task("下载中...", total=total_size)
                            downloaded = 0
                            for chunk in response.iter_bytes(chunk_size=8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                                progress.update(task, completed=downloaded)
                    else:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
    except Exception as e:
        console.print("[red]下载模板失败[/red]")
        detail = str(e)
        if zip_path.exists():
            zip_path.unlink()
        console.print(Panel(detail, title="下载失败", border_style="red"))
        raise typer.Exit(1)
    if verbose:
        console.print(f"已下载：{filename}")
    metadata = {
        "filename": filename,
        "size": file_size,
        "release": release_data["tag_name"],
        "asset_url": download_url
    }
    return zip_path, metadata

def download_and_extract_template(project_path: Path, ai_assistant: str, script_type: str, is_current_dir: bool = False, *, verbose: bool = True, tracker: StepTracker | None = None, client: httpx.Client = None, debug: bool = False, github_token: str = None) -> Path:
    """Download the latest release and extract it to create a new project.
    Returns project_path. Uses tracker if provided (with keys: fetch, download, extract, cleanup)
    """
    current_dir = Path.cwd()

    if tracker:
        tracker.start("fetch", "contacting GitHub API")
    try:
        zip_path, meta = download_template_from_github(
            ai_assistant,
            current_dir,
            script_type=script_type,
            verbose=verbose and tracker is None,
            show_progress=(tracker is None),
            client=client,
            debug=debug,
            github_token=github_token
        )
        if tracker:
            tracker.complete("fetch", f"release {meta['release']} ({meta['size']:,} bytes)")
            tracker.add("download", "Download template")
            tracker.complete("download", meta['filename'])
    except Exception as e:
        if tracker:
            tracker.error("fetch", str(e))
        else:
            if verbose:
                console.print(f"[red]下载模板出错：[/red] {e}")
        raise

    if tracker:
        tracker.add("extract", "Extract template")
        tracker.start("extract")
    elif verbose:
        console.print("Extracting template...")

    try:
        if not is_current_dir:
            project_path.mkdir(parents=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_contents = zip_ref.namelist()
            if tracker:
                tracker.start("zip-list")
                tracker.complete("zip-list", f"{len(zip_contents)} entries")
            elif verbose:
                console.print(f"[cyan]ZIP contains {len(zip_contents)} items[/cyan]")

            if is_current_dir:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    zip_ref.extractall(temp_path)

                    extracted_items = list(temp_path.iterdir())
                    if tracker:
                        tracker.start("extracted-summary")
                        tracker.complete("extracted-summary", f"temp {len(extracted_items)} items")
                    elif verbose:
                        console.print(f"[cyan]Extracted {len(extracted_items)} items to temp location[/cyan]")

                    source_dir = temp_path
                    if len(extracted_items) == 1 and extracted_items[0].is_dir():
                        source_dir = extracted_items[0]
                        if tracker:
                            tracker.add("flatten", "Flatten nested directory")
                            tracker.complete("flatten")
                        elif verbose:
                            console.print("[cyan]Found nested directory structure[/cyan]")

                    for item in source_dir.iterdir():
                        dest_path = project_path / item.name
                        if item.is_dir():
                            if dest_path.exists():
                                if verbose and not tracker:
                                    console.print(f"[yellow]Merging directory:[/yellow] {item.name}")
                                for sub_item in item.rglob('*'):
                                    if sub_item.is_file():
                                        rel_path = sub_item.relative_to(item)
                                        dest_file = dest_path / rel_path
                                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                                        # Special handling for .vscode/settings.json - merge instead of overwrite
                                        if dest_file.name == "settings.json" and dest_file.parent.name == ".vscode":
                                            handle_vscode_settings(sub_item, dest_file, rel_path, verbose, tracker)
                                        else:
                                            shutil.copy2(sub_item, dest_file)
                            else:
                                shutil.copytree(item, dest_path)
                        else:
                            if dest_path.exists() and verbose and not tracker:
                                console.print(f"[yellow]Overwriting file:[/yellow] {item.name}")
                            shutil.copy2(item, dest_path)
                    if verbose and not tracker:
                        console.print("[cyan]Template files merged into current directory[/cyan]")
            else:
                zip_ref.extractall(project_path)

                extracted_items = list(project_path.iterdir())
                if tracker:
                    tracker.start("extracted-summary")
                    tracker.complete("extracted-summary", f"{len(extracted_items)} top-level items")
                elif verbose:
                    console.print(f"[cyan]Extracted {len(extracted_items)} items to {project_path}:[/cyan]")
                    for item in extracted_items:
                        console.print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")

                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    nested_dir = extracted_items[0]
                    temp_move_dir = project_path.parent / f"{project_path.name}_temp"

                    shutil.move(str(nested_dir), str(temp_move_dir))

                    project_path.rmdir()

                    shutil.move(str(temp_move_dir), str(project_path))
                    if tracker:
                        tracker.add("flatten", "Flatten nested directory")
                        tracker.complete("flatten")
                    elif verbose:
                        console.print("[cyan]Flattened nested directory structure[/cyan]")

    except Exception as e:
        if tracker:
            tracker.error("extract", str(e))
        else:
            if verbose:
                console.print(f"[red]解压模板出错：[/red] {e}")
                if debug:
                    console.print(Panel(str(e), title="解压错误", border_style="red"))

        if not is_current_dir and project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(1)
    else:
        if tracker:
            tracker.complete("extract")
    finally:
        if tracker:
            tracker.add("cleanup", "清理临时压缩包")

        if zip_path.exists():
            zip_path.unlink()
            if tracker:
                tracker.complete("cleanup")
            elif verbose:
                console.print(f"已清理：{zip_path.name}")

    return project_path


def ensure_executable_scripts(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Ensure POSIX .sh scripts under .specify/scripts (recursively) have execute bits (no-op on Windows)."""
    if os.name == "nt":
        return  # Windows: skip silently
    scripts_root = project_path / ".specify" / "scripts"
    if not scripts_root.is_dir():
        return
    failures: list[str] = []
    updated = 0
    for script in scripts_root.rglob("*.sh"):
        try:
            if script.is_symlink() or not script.is_file():
                continue
            try:
                with script.open("rb") as f:
                    if f.read(2) != b"#!":
                        continue
            except Exception:
                continue
            st = script.stat()
            mode = st.st_mode
            if mode & 0o111:
                continue
            new_mode = mode
            if mode & 0o400:
                new_mode |= 0o100
            if mode & 0o040:
                new_mode |= 0o010
            if mode & 0o004:
                new_mode |= 0o001
            if not (new_mode & 0o100):
                new_mode |= 0o100
            os.chmod(script, new_mode)
            updated += 1
        except Exception as e:
            failures.append(f"{script.relative_to(scripts_root)}: {e}")
    if tracker:
        detail = f"{updated} updated" + (f", {len(failures)} failed" if failures else "")
        tracker.add("chmod", "Set script permissions recursively")
        (tracker.error if failures else tracker.complete)("chmod", detail)
    else:
        if updated:
            console.print(f"[cyan]Updated execute permissions on {updated} script(s) recursively[/cyan]")
        if failures:
            console.print("[yellow]Some scripts could not be updated:[/yellow]")
            for f in failures:
                console.print(f"  - {f}")

def ensure_constitution_from_template(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Copy constitution template to memory if it doesn't exist (preserves existing constitution on reinitialization)."""
    memory_constitution = project_path / ".specify" / "memory" / "constitution.md"
    template_constitution = project_path / ".specify" / "templates" / "constitution-template.md"

    # If constitution already exists in memory, preserve it
    if memory_constitution.exists():
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.skip("constitution", "existing file preserved")
        return

    # If template doesn't exist, something went wrong with extraction
    if not template_constitution.exists():
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.error("constitution", "template not found")
        return

    # Copy template to memory directory
    try:
        memory_constitution.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_constitution, memory_constitution)
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.complete("constitution", "copied from template")
        else:
            console.print("[cyan]已从模板初始化章程[/cyan]")
    except Exception as e:
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.error("constitution", str(e))
        else:
            console.print(f"[yellow]警告：无法初始化章程：{e}[/yellow]")

# Agent-specific skill directory overrides for agents whose skills directory
# doesn't follow the standard <agent_folder>/skills/ pattern
AGENT_SKILLS_DIR_OVERRIDES = {
    "codex": ".agents/skills",  # Codex agent layout override
}

# Default skills directory for agents not in AGENT_CONFIG
DEFAULT_SKILLS_DIR = ".agents/skills"

# Enhanced descriptions for each spec-kit command skill
SKILL_DESCRIPTIONS = {
    "specify": "Create or update feature specifications from natural language descriptions. Use when starting new features or refining requirements. Generates spec.md with user stories, functional requirements, and acceptance criteria following spec-driven development methodology.",
    "plan": "Generate technical implementation plans from feature specifications. Use after creating a spec to define architecture, tech stack, and implementation phases. Creates plan.md with detailed technical design.",
    "tasks": "Break down implementation plans into actionable task lists. Use after planning to create a structured task breakdown. Generates tasks.md with ordered, dependency-aware tasks.",
    "implement": "Execute all tasks from the task breakdown to build the feature. Use after task generation to systematically implement the planned solution following TDD approach where applicable.",
    "analyze": "Perform cross-artifact consistency analysis across spec.md, plan.md, and tasks.md. Use after task generation to identify gaps, duplications, and inconsistencies before implementation.",
    "clarify": "Structured clarification workflow for underspecified requirements. Use before planning to resolve ambiguities through coverage-based questioning. Records answers in spec clarifications section.",
    "constitution": "Create or update project governing principles and development guidelines. Use at project start to establish code quality, testing standards, and architectural constraints that guide all development.",
    "checklist": "Generate custom quality checklists for validating requirements completeness and clarity. Use to create unit tests for English that ensure spec quality before implementation.",
    "taskstoissues": "Convert tasks from tasks.md into GitHub issues. Use after task breakdown to track work items in GitHub project management.",
}


def _get_skills_dir(project_path: Path, selected_ai: str) -> Path:
    """Resolve the agent-specific skills directory for the given AI assistant.

    Uses ``AGENT_SKILLS_DIR_OVERRIDES`` first, then falls back to
    ``AGENT_CONFIG[agent]["folder"] + "skills"``, and finally to
    ``DEFAULT_SKILLS_DIR``.
    """
    if selected_ai in AGENT_SKILLS_DIR_OVERRIDES:
        return project_path / AGENT_SKILLS_DIR_OVERRIDES[selected_ai]

    agent_config = AGENT_CONFIG.get(selected_ai, {})
    agent_folder = agent_config.get("folder", "")
    if agent_folder:
        return project_path / agent_folder.rstrip("/") / "skills"

    return project_path / DEFAULT_SKILLS_DIR


def install_ai_skills(project_path: Path, selected_ai: str, tracker: StepTracker | None = None) -> bool:
    """Install Prompt.MD files from templates/commands/ as agent skills.

    Skills are written to the agent-specific skills directory following the
    `agentskills.io <https://agentskills.io/specification>`_ specification.
    Installation is additive — existing files are never removed and prompt
    command files in the agent's commands directory are left untouched.

    Args:
        project_path: Target project directory.
        selected_ai: AI assistant key from ``AGENT_CONFIG``.
        tracker: Optional progress tracker.

    Returns:
        ``True`` if at least one skill was installed or all skills were
        already present (idempotent re-run), ``False`` otherwise.
    """
    # Locate command templates in the agent's extracted commands directory.
    # download_and_extract_template() already placed the .md files here.
    agent_config = AGENT_CONFIG.get(selected_ai, {})
    agent_folder = agent_config.get("folder", "")
    commands_subdir = agent_config.get("commands_subdir", "commands")
    if agent_folder:
        templates_dir = project_path / agent_folder.rstrip("/") / commands_subdir
    else:
        templates_dir = project_path / commands_subdir

    def _supported_command_files(directory: Path) -> list[Path]:
        return sorted([*directory.glob("*.md"), *directory.glob("*.toml")])

    def _parse_command_template(command_file: Path) -> tuple[dict, str, str]:
        content = command_file.read_text(encoding="utf-8")

        if command_file.suffix == ".toml":
            if tomllib is not None:
                data = tomllib.loads(content)
            else:
                data = {}
                desc_match = re.search(r'^\s*description\s*=\s*"(?P<value>.*?)"\s*$', content, re.M)
                prompt_match = re.search(r'^\s*prompt\s*=\s*"""\n(?P<value>.*?)\n"""\s*$', content, re.S | re.M)
                if desc_match:
                    data["description"] = desc_match.group("value")
                if prompt_match:
                    data["prompt"] = prompt_match.group("value")
            frontmatter = {"description": data.get("description", "")}
            body = data.get("prompt", "").strip()
            return frontmatter, body, command_file.stem

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                if not isinstance(frontmatter, dict):
                    frontmatter = {}
                body = parts[2].strip()
            else:
                console.print(f"[yellow]警告：{command_file.name} 的 frontmatter 不完整（缺少结束 ---），将按纯文本处理[/yellow]")
                frontmatter = {}
                body = content
        else:
            frontmatter = {}
            body = content

        return frontmatter, body, command_file.stem

    if not templates_dir.exists() or not _supported_command_files(templates_dir):
        script_dir = Path(__file__).parent.parent.parent
        fallback_dir = script_dir / "templates" / "commands"
        if fallback_dir.exists() and _supported_command_files(fallback_dir):
            templates_dir = fallback_dir

    if not templates_dir.exists() or not _supported_command_files(templates_dir):
        if tracker:
            tracker.error("ai-skills", "未找到命令模板")
        else:
            console.print("[yellow]警告：未找到命令模板，跳过 skills 安装[/yellow]")
        return False

    command_files = _supported_command_files(templates_dir)
    if not command_files:
        if tracker:
            tracker.skip("ai-skills", "没有可用命令模板")
        else:
            console.print("[yellow]没有可安装的命令模板[/yellow]")
        return False

    # Resolve the correct skills directory for this agent
    skills_dir = _get_skills_dir(project_path, selected_ai)
    skills_dir.mkdir(parents=True, exist_ok=True)

    if tracker:
        tracker.start("ai-skills")

    installed_count = 0
    skipped_count = 0
    for command_file in command_files:
        try:
            frontmatter, body, command_name = _parse_command_template(command_file)
            # Normalize: extracted commands may be named "speckit.<cmd>.md";
            # strip the "speckit." prefix so skill names stay clean and
            # SKILL_DESCRIPTIONS lookups work.
            if command_name.startswith("speckit."):
                command_name = command_name[len("speckit."):]
            skill_name = f"speckit-{command_name}"

            # Create skill directory (additive — never removes existing content)
            skill_dir = skills_dir / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)

            # Select the best description available
            original_desc = frontmatter.get("description", "")
            enhanced_desc = SKILL_DESCRIPTIONS.get(command_name, original_desc or f"Spec Kit 工作流命令：{command_name}")

            # Build SKILL.md following agentskills.io spec
            # Use yaml.safe_dump to safely serialise the frontmatter and
            # avoid YAML injection from descriptions containing colons,
            # quotes, or newlines.
            # Normalize source filename for metadata — strip speckit. prefix
            # so it matches the canonical templates/commands/<cmd>.md path.
            source_name = command_file.name
            if source_name.startswith("speckit."):
                source_name = source_name[len("speckit."):]

            frontmatter_data = {
                "name": skill_name,
                "description": enhanced_desc,
                "compatibility": "Requires spec-kit project structure with .specify/ directory",
                "metadata": {
                    "author": "github-spec-kit",
                    "source": f"templates/commands/{source_name}",
                },
            }
            frontmatter_text = yaml.safe_dump(frontmatter_data, sort_keys=False).strip()
            skill_content = (
                f"---\n"
                f"{frontmatter_text}\n"
                f"---\n\n"
                f"# Speckit {command_name.title()} Skill\n\n"
                f"{body}\n"
            )

            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                # Do not overwrite user-customized skills on re-runs
                skipped_count += 1
                continue
            skill_file.write_text(skill_content, encoding="utf-8")
            installed_count += 1

        except Exception as e:
            console.print(f"[yellow]警告：安装 skill {command_file.stem} 失败：{e}[/yellow]")
            continue

    if tracker:
        if installed_count > 0 and skipped_count > 0:
            tracker.complete("ai-skills", f"{installed_count} new + {skipped_count} existing skills in {skills_dir.relative_to(project_path)}")
        elif installed_count > 0:
            tracker.complete("ai-skills", f"{installed_count} skills → {skills_dir.relative_to(project_path)}")
        elif skipped_count > 0:
            tracker.complete("ai-skills", f"{skipped_count} skills already present")
        else:
            tracker.error("ai-skills", "未安装任何 skills")
    else:
        if installed_count > 0:
            console.print(f"[green]✓[/green] 已安装 {installed_count} 个 agent skills 到 {skills_dir.relative_to(project_path)}/")
        elif skipped_count > 0:
            console.print(f"[green]✓[/green] {skills_dir.relative_to(project_path)}/ 中已有 {skipped_count} 个 agent skills")
        else:
            console.print("[yellow]未安装任何 skills[/yellow]")

    return installed_count > 0 or skipped_count > 0


def _print_json_error(msg: str):
    import sys, json
    sys.stdout.write(json.dumps({"status": "error", "message": msg}) + "\n")

@app.command()
def init(
    project_name: Optional[str] = typer.Argument(None, help="新项目目录名称（使用 --here 时可省略，也可用 '.' 表示当前目录）"),
    ai_assistant: str = typer.Option(None, "--ai", help=AI_ASSISTANT_HELP),
    ai_commands_dir: str = typer.Option(None, "--ai-commands-dir", help="agent 命令文件目录（使用 --ai generic 时必填，例如 .myagent/commands/）"),
    script_type: str = typer.Option(None, "--script", help="使用的脚本类型：sh 或 ps"),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools", help="跳过 Claude Code 等 AI 工具的检测"),
    no_git: bool = typer.Option(False, "--no-git", help="跳过 git 仓库初始化"),
    here: bool = typer.Option(False, "--here", help="在当前目录初始化项目，而不是创建新目录"),
    force: bool = typer.Option(False, "--force", help="搭配 --here 使用时强制合并/覆盖（跳过确认）"),
    skip_tls: bool = typer.Option(False, "--skip-tls", help="跳过 SSL/TLS 校验（不推荐）"),
    debug: bool = typer.Option(False, "--debug", help="显示网络与解压失败的详细诊断信息"),
    github_token: str = typer.Option(None, "--github-token", help="用于 API 请求的 GitHub Token（也可通过 GH_TOKEN 或 GITHUB_TOKEN 设置）"),
    ai_skills: bool = typer.Option(False, "--ai-skills", help="将 Prompt.MD 模板安装为 agent skills（需搭配 --ai）"),
    dry_run: bool = typer.Option(False, "--dry-run", help="预览将要创建的文件清单，不执行实际写入"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出初始化结果，不显示交互式进度"),
):
    """
    使用最新模板初始化一个新的 Specify 项目。

    此命令会：
    1. 检查必需工具是否已安装（git 为可选）
    2. 让你选择 AI 助手
    3. 从 GitHub 下载对应模板
    4. 将模板解压到新项目目录或当前目录
    5. 初始化新的 git 仓库（如果未使用 --no-git 且当前不存在仓库）
    6. 可选地安装 agent skills

    示例：
        specify-zh init my-project
        specify-zh init my-project --ai claude
        specify-zh init my-project --ai copilot --no-git
        specify-zh init --ignore-agent-tools my-project
        specify-zh init . --ai claude         # Initialize in current directory
        specify-zh init .                     # Initialize in current directory (interactive AI selection)
        specify-zh init --here --ai claude    # Alternative syntax for current directory
        specify-zh init --here --ai codex
        specify-zh init --here --ai codebuddy
        specify-zh init --here --ai vibe      # Initialize with Mistral Vibe support
        specify-zh init --here
        specify-zh init --here --force  # Skip confirmation when current directory not empty
        specify-zh init my-project --ai claude --ai-skills   # Install agent skills
        specify-zh init --here --ai gemini --ai-skills
        specify-zh init my-project --ai generic --ai-commands-dir .myagent/commands/  # 自定义 agent
    """

    if json_output:
        import io
        global console
        console.file = io.StringIO()

    show_banner()

    # Detect when option values are likely misinterpreted flags (parameter ordering issue)
    if ai_assistant and ai_assistant.startswith("--"):
        console.print(f"[red]Error:[/red] Invalid value for --ai: '{ai_assistant}'")
        console.print("[yellow]提示：[/yellow] 你可能忘了给 --ai 提供取值。")
        console.print("[yellow]示例：[/yellow] specify-zh init --ai claude --here")
        console.print(f"[yellow]可用 agents：[/yellow] {', '.join(AGENT_CONFIG.keys())}")
        if json_output:
            _print_json_error(f"Invalid value for --ai: '{ai_assistant}'")
        raise typer.Exit(1)
    
    if ai_commands_dir and ai_commands_dir.startswith("--"):
        console.print(f"[red]Error:[/red] Invalid value for --ai-commands-dir: '{ai_commands_dir}'")
        console.print("[yellow]提示：[/yellow] 你可能忘了给 --ai-commands-dir 提供取值。")
        console.print("[yellow]示例：[/yellow] specify-zh init --ai generic --ai-commands-dir .myagent/commands/")
        raise typer.Exit(1)

    if ai_assistant:
        ai_assistant = AI_ASSISTANT_ALIASES.get(ai_assistant, ai_assistant)

    if project_name == ".":
        here = True
        project_name = None  # Clear project_name to use existing validation logic

    if here and project_name:
        console.print("[red]错误：[/red] 不能同时指定项目名和 --here")
        if json_output: _print_json_error("不能同时指定项目名和 --here")
        raise typer.Exit(1)

    if not here and not project_name:
        if sys.stdin.isatty() and not json_output:
            project_name = typer.prompt("请输入新项目目录名称（或输入 '.' 在当前目录初始化）")
            if project_name == ".":
                here = True
                project_name = None
        else:
            console.print("[red]错误：[/red] 必须提供项目名，或使用 '.' 表示当前目录，或使用 --here")
            if json_output: _print_json_error("必须提供项目名")
            raise typer.Exit(1)

    if ai_skills and not ai_assistant:
        console.print("[red]错误：[/red] --ai-skills 必须搭配 --ai 使用")
        console.print("[yellow]Usage:[/yellow] specify-zh init <project> --ai <agent> --ai-skills")
        raise typer.Exit(1)

    if here:
        project_name = Path.cwd().name
        project_path = Path.cwd()

        target_spec_dir = project_path / ".specify"
        if target_spec_dir.exists():
            console.print("[yellow]警告：[/yellow] 目标路径已存在 .specify/ 目录（项目可能已初始化）。")
            if not force and not json_output:
                response = typer.confirm("检测到已初始化的项目，是否覆盖？", default=False)
                if not response:
                    console.print("[yellow]已取消操作[/yellow]")
                    raise typer.Exit(0)
        else:
            existing_items = list(project_path.iterdir())
            if existing_items:
                console.print(f"[yellow]警告：[/yellow] 当前目录非空（{len(existing_items)} 个条目）")
                console.print("[yellow]模板文件会与现有内容合并，并可能覆盖已有文件[/yellow]")
                if force or json_output:
                    console.print("[cyan]已提供 --force 或 --json：跳过确认，直接继续合并[/cyan]")
                else:
                    response = typer.confirm("是否继续？")
                    if not response:
                        console.print("[yellow]已取消操作[/yellow]")
                        raise typer.Exit(0)
    else:
        project_path = Path(project_name).resolve()
        if project_path.exists():
            target_spec_dir = project_path / ".specify"
            if target_spec_dir.exists():
                console.print("[yellow]警告：[/yellow] 目标路径已存在 .specify/ 目录（项目可能已初始化）。")
                if not force and not json_output:
                    response = typer.confirm("检测到已初始化的项目，是否覆盖？", default=False)
                    if not response:
                        console.print("[yellow]已取消操作[/yellow]")
                        raise typer.Exit(0)
            else:
                error_panel = Panel(
                    f"Directory '[cyan]{project_name}[/cyan]' already exists\n"
                    "请选择其他项目名称，或先移除现有目录。",
                    title="[red]目录冲突[/red]",
                    border_style="red",
                    padding=(1, 2)
                )
                console.print()
                console.print(error_panel)
                if json_output: _print_json_error("目录冲突：已有同名非空目录")
                raise typer.Exit(1)

    current_dir = Path.cwd()

    setup_lines = [
        "[cyan]Specify 项目设置[/cyan]",
        "",
        f"{'项目':<15} [green]{project_path.name}[/green]",
        f"{'工作路径':<15} [dim]{current_dir}[/dim]",
    ]

    if not here:
        setup_lines.append(f"{'目标路径':<15} [dim]{project_path}[/dim]")

    console.print(Panel("\n".join(setup_lines), border_style="cyan", padding=(1, 2)))

    should_init_git = False
    if not no_git:
        should_init_git = check_tool("git")
        if not should_init_git:
            console.print("[yellow]未检测到 git，将跳过仓库初始化[/yellow]")

    if ai_assistant:
        if ai_assistant not in AGENT_CONFIG:
            console.print(f"[red]错误：[/red] 无效的 AI 助手 '{ai_assistant}'。可选值：{', '.join(AGENT_CONFIG.keys())}")
            raise typer.Exit(1)
        selected_ai = ai_assistant
    else:
        # Create options dict for selection (agent_key: display_name)
        ai_choices = {
            key: f"{config['name']} " + ("[dim](CLI 工具)[/dim]" if config.get("requires_cli") else "[dim](IDE 扩展)[/dim]")
            for key, config in AGENT_CONFIG.items() if key != "generic"
        }
        ai_choices["generic"] = "Custom Agent [dim](自定义)[/dim]"
        selected_ai = select_with_arrows(
            ai_choices, 
            "选择你的 AI 助手：", 
            "copilot"
        )

    # Validate --ai-commands-dir usage
    if selected_ai == "generic":
        if not ai_commands_dir:
            console.print("[red]错误：[/red] 使用 --ai generic 时必须提供 --ai-commands-dir")
            console.print("[dim]Example: specify-zh init my-project --ai generic --ai-commands-dir .myagent/commands/[/dim]")
            raise typer.Exit(1)
    elif ai_commands_dir:
        console.print(f"[red]Error:[/red] --ai-commands-dir can only be used with --ai generic (not '{selected_ai}')")
        raise typer.Exit(1)

    if not ignore_agent_tools:
        agent_config = AGENT_CONFIG.get(selected_ai)
        if agent_config and agent_config["requires_cli"]:
            install_url = agent_config["install_url"]
            if not check_tool(selected_ai):
                error_panel = Panel(
                    f"[cyan]{selected_ai}[/cyan] not found\n"
                    f"Install from: [cyan]{install_url}[/cyan]\n"
                    f"{agent_config['name']} is required to continue with this project type.\n\n"
                    "提示：使用 [cyan]--ignore-agent-tools[/cyan] 可跳过该检查",
                    title="[red]Agent 检测失败[/red]",
                    border_style="red",
                    padding=(1, 2)
                )
                console.print()
                console.print(error_panel)
                raise typer.Exit(1)

    if script_type:
        if script_type not in SCRIPT_TYPE_CHOICES:
            console.print(f"[red]错误：[/red] 无效的脚本类型 '{script_type}'。可选值：{', '.join(SCRIPT_TYPE_CHOICES.keys())}")
            raise typer.Exit(1)
        selected_script = script_type
    else:
        default_script = "ps" if os.name == "nt" else "sh"

        if sys.stdin.isatty():
            selected_script = select_with_arrows(SCRIPT_TYPE_CHOICES, "选择脚本类型（或按 Enter）", default_script)
        else:
            selected_script = default_script

    console.print(f"[cyan]已选择 AI 助手：[/cyan] {selected_ai}")
    console.print(f"[cyan]已选择脚本类型：[/cyan] {selected_script}")

    tracker = StepTracker("初始化 Specify 项目")

    sys._specify_tracker_active = True

    tracker.add("precheck", "Check required tools")
    tracker.complete("precheck", "ok")
    tracker.add("ai-select", "Select AI assistant")
    tracker.complete("ai-select", f"{selected_ai}")
    tracker.add("script-select", "Select script type")
    tracker.complete("script-select", selected_script)
    for key, label in [
        ("fetch", "获取最新发布"),
        ("download", "下载模板"),
        ("extract", "解压模板"),
        ("zip-list", "归档内容"),
        ("extracted-summary", "解压摘要"),
        ("chmod", "确保脚本可执行"),
        ("constitution", "初始化章程"),
    ]:
        tracker.add(key, label)
    if ai_skills:
        tracker.add("ai-skills", "安装 agent skills")
    for key, label in [
        ("cleanup", "清理临时文件"),
        ("git", "初始化 git 仓库"),
        ("final", "完成")
    ]:
        tracker.add(key, label)

    # Track git error message outside Live context so it persists
    git_error_message = None

    if not force and not json_output and sys.stdin.isatty():
        console.print()
        response = typer.confirm("确认以上配置并开始初始化？", default=True)
        if not response:
            console.print("[yellow]已取消初始化[/yellow]")
            raise typer.Exit(0)

    if dry_run:
        console.print("\n[bold yellow]--- Dry Run 预览 ---[/bold yellow]")
        console.print(f"目标目录: {project_path}")
        console.print(f"AI 助手: {selected_ai}")
        console.print(f"脚本类型: {selected_script}")
        console.print(f"执行内容: 将下载并解压 {selected_ai} 模板")
        if ai_skills:
            console.print("执行内容: 将安装 agent skills")
        if not no_git and should_init_git:
            console.print("执行内容: 将初始化 git 仓库")
        
        if json_output:
            import sys
            json_data = {
                "status": "dry-run",
                "project_path": str(project_path),
                "ai_assistant": selected_ai,
                "script_type": selected_script,
                "ai_skills": ai_skills,
                "init_git": not no_git and should_init_git
            }
            sys.stdout.write(json.dumps(json_data, indent=2) + "\n")
        raise typer.Exit(0)

    with Live(tracker.render(), console=console, refresh_per_second=8, transient=True) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        try:
            verify = not skip_tls
            local_ssl_context = ssl_context if verify else False
            local_client = httpx.Client(verify=local_ssl_context)

            download_and_extract_template(project_path, selected_ai, selected_script, here, verbose=False, tracker=tracker, client=local_client, debug=debug, github_token=github_token)

            # For generic agent, rename placeholder directory to user-specified path
            if selected_ai == "generic" and ai_commands_dir:
                placeholder_dir = project_path / ".speckit" / "commands"
                target_dir = project_path / ai_commands_dir
                if placeholder_dir.is_dir():
                    target_dir.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(placeholder_dir), str(target_dir))
                    # Clean up empty .speckit dir if it's now empty
                    speckit_dir = project_path / ".speckit"
                    if speckit_dir.is_dir() and not any(speckit_dir.iterdir()):
                        speckit_dir.rmdir()

            ensure_executable_scripts(project_path, tracker=tracker)

            ensure_constitution_from_template(project_path, tracker=tracker)

            if ai_skills:
                skills_ok = install_ai_skills(project_path, selected_ai, tracker=tracker)

                # When --ai-skills is used on a NEW project and skills were
                # successfully installed, remove the command files that the
                # template archive just created.  Skills replace commands, so
                # keeping both would be confusing.  For --here on an existing
                # repo we leave pre-existing commands untouched to avoid a
                # breaking change.  We only delete AFTER skills succeed so the
                # project always has at least one of {commands, skills}.
                if skills_ok and not here:
                    agent_cfg = AGENT_CONFIG.get(selected_ai, {})
                    agent_folder = agent_cfg.get("folder", "")
                    commands_subdir = agent_cfg.get("commands_subdir", "commands")
                    if agent_folder:
                        cmds_dir = project_path / agent_folder.rstrip("/") / commands_subdir
                        if cmds_dir.exists():
                            try:
                                shutil.rmtree(cmds_dir)
                            except OSError:
                                # Best-effort cleanup: skills are already installed,
                                # so leaving stale commands is non-fatal.
                                console.print("[yellow]警告：无法删除已提取的命令目录[/yellow]")

            if not no_git:
                tracker.start("git")
                if is_git_repo(project_path):
                    tracker.complete("git", "existing repo detected")
                elif should_init_git:
                    success, error_msg = init_git_repo(project_path, quiet=True)
                    if success:
                        tracker.complete("git", "initialized")
                    else:
                        tracker.error("git", "init failed")
                        git_error_message = error_msg
                else:
                    tracker.skip("git", "git not available")
            else:
                tracker.skip("git", "--no-git flag")

            tracker.complete("final", "project ready")
        except Exception as e:
            tracker.error("final", str(e))
            console.print(Panel(f"初始化失败：{e}", title="失败", border_style="red"))
            if debug:
                _env_pairs = [
                    ("Python", sys.version.split()[0]),
                    ("Platform", sys.platform),
                    ("CWD", str(Path.cwd())),
                ]
                _label_width = max(len(k) for k, _ in _env_pairs)
                env_lines = [f"{k.ljust(_label_width)} → [bright_black]{v}[/bright_black]" for k, v in _env_pairs]
                console.print(Panel("\n".join(env_lines), title="调试环境", border_style="magenta"))
            if not here and project_path.exists():
                shutil.rmtree(project_path)
            raise typer.Exit(1)
        finally:
            pass

    console.print(tracker.render())
    console.print("\n[bold green]项目已就绪。[/bold green]")
    
    # Show git error details if initialization failed
    if git_error_message:
        console.print()
        git_error_panel = Panel(
            f"[yellow]警告：[/yellow] Git 仓库初始化失败\n\n"
            f"{git_error_message}\n\n"
            f"[dim]你可以稍后手动初始化 git：[/dim]\n"
            f"[cyan]cd {project_path if not here else '.'}[/cyan]\n"
            f"[cyan]git init[/cyan]\n"
            f"[cyan]git add .[/cyan]\n"
            f"[cyan]git commit -m \"Initial commit\"[/cyan]",
            title="[red]Git 初始化失败[/red]",
            border_style="red",
            padding=(1, 2)
        )
        console.print(git_error_panel)

    # Agent folder security notice
    agent_config = AGENT_CONFIG.get(selected_ai)
    if agent_config:
        agent_folder = ai_commands_dir if selected_ai == "generic" else agent_config["folder"]
        if agent_folder:
            security_notice = Panel(
                f"部分 agents 可能会在项目内的 agent 目录中保存凭据、认证令牌或其他可识别的私密信息。\n"
                f"建议将 [cyan]{agent_folder}[/cyan]（或其中的敏感部分）加入 [cyan].gitignore[/cyan]，避免误提交凭据。",
                title="[yellow]Agent 目录安全提示[/yellow]",
                border_style="yellow",
                padding=(1, 2)
            )
            console.print()
            console.print(security_notice)

    steps_lines = []
    if not here:
        steps_lines.append(f"1. 进入项目目录：[cyan]cd {project_name}[/cyan]")
        step_num = 2
    else:
        steps_lines.append("1. 你已经位于项目目录中。")
        step_num = 2

    # Add Codex-specific setup step if needed
    if selected_ai == "codex":
        codex_path = project_path / ".codex"
        quoted_path = shlex.quote(str(codex_path))
        if os.name == "nt":  # Windows
            cmd = f"setx CODEX_HOME {quoted_path}"
        else:  # Unix-like systems
            cmd = f"export CODEX_HOME={quoted_path}"
        
        steps_lines.append(f"{step_num}. 在运行 Codex 前设置 [cyan]CODEX_HOME[/cyan] 环境变量：[cyan]{cmd}[/cyan]")
        step_num += 1

    steps_lines.append(f"{step_num}. 开始使用 slash commands 与你的 AI 助手协作：")

    steps_lines.append("   2.1 [cyan]/speckit.constitution[/] - 建立项目原则")
    steps_lines.append("   2.2 [cyan]/speckit.specify[/] - 创建基础规范")
    steps_lines.append("   2.3 [cyan]/speckit.plan[/] - 生成实施计划")
    steps_lines.append("   2.4 [cyan]/speckit.tasks[/] - 生成可执行任务")
    steps_lines.append("   2.5 [cyan]/speckit.implement[/] - 执行实施")

    steps_panel = Panel("\n".join(steps_lines), title="后续步骤", border_style="cyan", padding=(1,2))
    console.print()
    console.print(steps_panel)

    enhancement_lines = [
        "这些是可选命令，可用于提升规范质量与信心 [bright_black](improve quality & confidence)[/bright_black]",
        "",
        "○ [cyan]/speckit.clarify[/] [bright_black](可选)[/bright_black] - 在规划前用结构化提问消除模糊点（若使用，请在 [cyan]/speckit.plan[/] 前执行）",
        "○ [cyan]/speckit.analyze[/] [bright_black](可选)[/bright_black] - 生成跨制品一致性与对齐分析（在 [cyan]/speckit.tasks[/] 之后、[cyan]/speckit.implement[/] 之前执行）",
        "○ [cyan]/speckit.checklist[/] [bright_black](可选)[/bright_black] - 生成质量检查清单，验证需求完整性、清晰度与一致性（在 [cyan]/speckit.plan[/] 之后执行）"
    ]
    enhancements_panel = Panel("\n".join(enhancement_lines), title="增强命令", border_style="cyan", padding=(1,2))
    console.print()
    console.print(enhancements_panel)

@app.command()
def check():
    """检查所需工具是否已安装。"""
    show_banner()
    console.print("[bold]正在检查 specify-zh 运行环境...[/bold]\n")

    tracker = StepTracker("specify-zh 环境检查")

    tracker.add("git", "Git 版本控制")
    git_ok = check_tool("git", tracker=tracker)

    agent_results = {}
    for agent_key, agent_config in AGENT_CONFIG.items():
        if agent_key == "generic":
            continue  # Generic is not a real agent to check
        agent_name = agent_config["name"]
        requires_cli = agent_config["requires_cli"]

        tracker.add(agent_key, agent_name)

        if requires_cli:
            agent_results[agent_key] = check_tool(agent_key, tracker=tracker)
        else:
            # IDE-based agent - skip CLI check and mark as optional
            tracker.skip(agent_key, "[dim]IDE 型，跳过[/dim]")
            agent_results[agent_key] = False  # Don't count IDE agents as "found"

    # Check VS Code variants (not in agent config)
    tracker.add("code", "Visual Studio Code")
    check_tool("code", tracker=tracker)

    tracker.add("code-insiders", "Visual Studio Code Insiders")
    check_tool("code-insiders", tracker=tracker)

    console.print(tracker.render())

    # --- P1-9: Summary Panel ---
    cli_agents = [k for k, v in AGENT_CONFIG.items() if v.get("requires_cli")]
    ide_agents = [k for k, v in AGENT_CONFIG.items() if not v.get("requires_cli") and k != "generic"]
    
    total_cli_count = len(cli_agents)
    installed_cli_count = sum(1 for k in cli_agents if agent_results.get(k))
    missing_cli_count = total_cli_count - installed_cli_count
    
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column("项目", style="cyan", justify="right")
    summary_table.add_column("数值", style="white")
    
    summary_table.add_row("已安装 CLI", f"{installed_cli_count}/{total_cli_count}")
    summary_table.add_row("缺失 CLI", f"{missing_cli_count}/{total_cli_count}")
    summary_table.add_row("IDE 型（无需 CLI）", str(len(ide_agents)))
    
    console.print()
    console.print(
        Panel(
            summary_table,
            title="[bold cyan]检测汇总[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
    )

    console.print("\n[bold green]specify-zh 已可使用！[/bold green]")

    if not git_ok:
        console.print("[dim]提示：安装 git 以启用仓库管理[/dim]")

    if missing_cli_count > 0:
        missing_names = [AGENT_CONFIG[k]["name"] for k in cli_agents if not agent_results.get(k)]
        # Recommend top 3 popular CLI tools
        popular = ["Claude Code", "Cursor", "Gemini CLI"]
        recommend = [n for n in popular if n in missing_names]
        if recommend:
            console.print(f"[dim]提示：推荐优先安装 CLI 工具（如 {', '.join(recommend[:3])}）以获得最佳体验[/dim]")
        elif not any(agent_results.values()):
            console.print("[dim]提示：安装 AI 助手可获得最佳体验[/dim]")


@app.command()
def doctor():
    """诊断当前环境与项目状态，并给出修复建议。"""
    show_banner()
    console.print("[bold]正在执行环境诊断...[/bold]\n")

    diagnostics = _collect_doctor_diagnostics(Path.cwd())

    tracker = StepTracker("环境与项目诊断")
    tracker.add("python", "Python")
    tracker.complete("python", diagnostics["python_version"])

    tracker.add("git", "Git")
    if diagnostics["git_available"]:
        tracker.complete("git", "可用")
    else:
        tracker.error("git", "未安装")

    tracker.add("uv", "uv")
    if diagnostics["uv_available"]:
        tracker.complete("uv", "可用")
    else:
        tracker.error("uv", "未安装")

    tracker.add("github-token", "GitHub Token")
    if diagnostics["has_github_token"]:
        tracker.complete("github-token", "已配置")
    else:
        tracker.skip("github-token", "未配置")

    tracker.add("github-api", "GitHub API")
    if diagnostics["github_connectivity_ok"]:
        tracker.complete("github-api", diagnostics["github_connectivity_detail"])
    else:
        tracker.error("github-api", diagnostics["github_connectivity_detail"])

    tracker.add("project", "当前目录")
    if diagnostics["is_spec_project"]:
        tracker.complete("project", "已检测到 .specify/")
    else:
        tracker.skip("project", "尚未初始化为 spec-kit 项目")

    tracker.add("repo", "Git 仓库")
    if diagnostics["is_git_repo"]:
        tracker.complete("repo", "当前目录位于 Git 仓库内")
    else:
        tracker.skip("repo", "未检测到 Git 仓库")

    tracker.add("agents", "AI CLI")
    if diagnostics["available_agent_count"] > 0:
        tracker.complete("agents", f"检测到 {diagnostics['available_agent_count']} 个可用 CLI")
    else:
        tracker.skip("agents", "尚未检测到可用的 AI CLI")

    console.print(tracker.render())
    console.print()

    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column("项", style="cyan", justify="right")
    summary_table.add_column("值", style="white")
    summary_table.add_row("当前路径", str(diagnostics["path"]))
    summary_table.add_row("分发包名", DIST_NAME if diagnostics["dist_ok"] else "[yellow]异常 (未找到安装记录)[/yellow]")
    summary_table.add_row("命令入口", diagnostics["cmd_path"] if diagnostics["cmd_path"] else "[yellow]异常 (不在 PATH 中)[/yellow]")
    summary_table.add_row("Spec Kit 项目", "是" if diagnostics["is_spec_project"] else "否")
    summary_table.add_row("Git 仓库", "是" if diagnostics["is_git_repo"] else "否")
    summary_table.add_row("GitHub Token", "已配置" if diagnostics["has_github_token"] else "未配置")
    summary_table.add_row("可用 AI CLI 数量", str(diagnostics["available_agent_count"]))
    if diagnostics["missing_agents"]:
        summary_table.add_row("缺失的 AI CLI", ", ".join(diagnostics["missing_agents"]))

    console.print(
        Panel(
            summary_table,
            title="[bold cyan]诊断摘要[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    recommendations = _build_doctor_recommendations(diagnostics)
    console.print()
    console.print(
        Panel(
            "\n".join(f"{idx}. {item}" for idx, item in enumerate(recommendations, start=1)),
            title="[bold yellow]建议的下一步[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
    )

    if diagnostics["is_spec_project"]:
        follow_up = [
            "1. 运行 `/speckit.constitution` 建立或校准项目原则",
            "2. 运行 `/speckit.specify` 明确需求与验收标准",
            "3. 运行 `/speckit.plan` 生成实施计划",
        ]
    else:
        follow_up = [
            "1. 运行 `specify-zh init --here --ai claude` 在当前目录初始化",
            "2. 或运行 `specify-zh init <项目名> --ai claude` 创建新项目",
            "3. 初始化完成后，再进入 slash commands 工作流",
        ]

    console.print()
    console.print(
        Panel(
            "\n".join(follow_up),
            title="[bold green]可直接执行的命令[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )

@app.command()
def version():
    """显示版本与系统信息。"""
    import platform
    import shutil

    show_banner()

    # Get CLI version and run mode from package metadata
    cli_version, run_source = _get_cli_distribution_version()
    run_mode = "已安装" if run_source == "installed" else "本地开发"

    # Detect specify-zh executable path
    cmd_path = shutil.which(CMD_NAME) or "未在 PATH 中找到"

    # Fetch latest template release version
    repo_owner = "github"
    repo_name = "spec-kit"
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    template_version = "unknown"
    release_date = "unknown"

    try:
        response = client.get(
            api_url,
            timeout=10,
            follow_redirects=True,
            headers=_github_auth_headers(),
        )
        if response.status_code == 200:
            release_data = response.json()
            template_version = release_data.get("tag_name", "unknown")
            # Remove 'v' prefix if present
            if template_version.startswith("v"):
                template_version = template_version[1:]
            release_date = release_data.get("published_at", "unknown")
            if release_date != "unknown":
                # Format the date nicely
                try:
                    dt = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                    release_date = dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
    except Exception:
        pass

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Key", style="cyan", justify="right")
    info_table.add_column("Value", style="white")

    info_table.add_row("分发包名", DIST_NAME)
    info_table.add_row("命令入口", CMD_NAME)
    info_table.add_row("CLI 版本", cli_version)
    info_table.add_row("运行模式", run_mode)
    info_table.add_row("", "")
    info_table.add_row("模板仓库", f"github/{repo_name}")
    info_table.add_row("模板版本", template_version)
    info_table.add_row("发布时间", release_date)
    info_table.add_row("", "")
    info_table.add_row("Python", platform.python_version())
    info_table.add_row("平台", platform.system())
    info_table.add_row("架构", platform.machine())
    info_table.add_row("系统版本", platform.version())

    panel = Panel(
        info_table,
        title="[bold cyan]specify-cli-zh 信息[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )

    console.print(panel)
    console.print()


# ===== Extension Commands =====

extension_app = typer.Typer(
    name="extension",
    help="管理 spec-kit 扩展",
    add_completion=False,
)
app.add_typer(extension_app, name="extension")

catalog_app = typer.Typer(
    name="catalog",
    help="管理扩展目录",
    add_completion=False,
)
extension_app.add_typer(catalog_app, name="catalog")


def get_speckit_version() -> str:
    """Get current spec-kit version."""
    version, _ = _get_cli_distribution_version()
    return version


@extension_app.command("list")
def extension_list(
    available: bool = typer.Option(False, "--available", help="显示目录中可用的扩展"),
    all_extensions: bool = typer.Option(False, "--all", help="同时显示已安装和可用扩展"),
):
    """列出已安装扩展。"""
    from .extensions import ExtensionManager

    project_root = Path.cwd()

    # Check if we're in a spec-kit project
    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]错误：[/red] 当前不是 spec-kit 项目（缺少 .specify/ 目录）")
        console.print("请在 spec-kit 项目根目录运行此命令")
        raise typer.Exit(1)

    manager = ExtensionManager(project_root)
    installed = manager.list_installed()

    if not installed and not (available or all_extensions):
        console.print("[yellow]当前没有安装任何扩展。[/yellow]")
        console.print("\n可使用以下命令安装扩展：")
        console.print("  specify-zh extension add <extension-name>")
        return

    if installed:
        console.print("\n[bold cyan]已安装扩展：[/bold cyan]\n")

        for ext in installed:
            status_icon = "✓" if ext["enabled"] else "✗"
            status_color = "green" if ext["enabled"] else "red"

            console.print(f"  [{status_color}]{status_icon}[/{status_color}] [bold]{ext['name']}[/bold] (v{ext['version']})")
            console.print(f"     {ext['description']}")
            console.print(f"     命令数：{ext['command_count']} | Hooks：{ext['hook_count']} | 状态：{'已启用' if ext['enabled'] else '已禁用'}")
            console.print()

    if available or all_extensions:
        console.print("\n安装扩展：")
        console.print("  [cyan]specify-zh extension add <name>[/cyan]")


@catalog_app.command("list")
def catalog_list():
    """列出所有启用中的扩展目录。"""
    from .extensions import ExtensionCatalog, ValidationError

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]错误：[/red] 当前不是 spec-kit 项目（缺少 .specify/ 目录）")
        console.print("请在 spec-kit 项目根目录运行此命令")
        raise typer.Exit(1)

    catalog = ExtensionCatalog(project_root)

    try:
        active_catalogs = catalog.get_active_catalogs()
    except ValidationError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]当前启用的扩展目录：[/bold cyan]\n")
    for entry in active_catalogs:
        install_str = (
            "[green]允许安装[/green]"
            if entry.install_allowed
            else "[yellow]仅发现，不可安装[/yellow]"
        )
        console.print(f"  [bold]{entry.name}[/bold]（优先级 {entry.priority}）")
        if entry.description:
            console.print(f"     {entry.description}")
        console.print(f"     URL：{entry.url}")
        console.print(f"     安装权限：{install_str}")
        console.print()

    config_path = project_root / ".specify" / "extension-catalogs.yml"
    user_config_path = Path.home() / ".specify" / "extension-catalogs.yml"
    if os.environ.get("SPECKIT_CATALOG_URL"):
        console.print("[dim]目录通过 SPECKIT_CATALOG_URL 环境变量配置。[/dim]")
    else:
        try:
            proj_loaded = config_path.exists() and catalog._load_catalog_config(config_path) is not None
        except ValidationError:
            proj_loaded = False
        if proj_loaded:
            console.print(f"[dim]配置文件：{config_path.relative_to(project_root)}[/dim]")
        else:
            try:
                user_loaded = user_config_path.exists() and catalog._load_catalog_config(user_config_path) is not None
            except ValidationError:
                user_loaded = False
            if user_loaded:
                console.print("[dim]配置文件：~/.specify/extension-catalogs.yml[/dim]")
            else:
                console.print("[dim]当前使用内置默认目录栈。[/dim]")
                console.print(
                    "[dim]如需自定义，请添加 .specify/extension-catalogs.yml。[/dim]"
                )


@catalog_app.command("add")
def catalog_add(
    url: str = typer.Argument(help="目录 URL（必须使用 HTTPS）"),
    name: str = typer.Option(..., "--name", help="目录名称"),
    priority: int = typer.Option(10, "--priority", help="优先级（值越小优先级越高）"),
    install_allowed: bool = typer.Option(
        False, "--install-allowed/--no-install-allowed",
        help="允许从该目录安装扩展",
    ),
    description: str = typer.Option("", "--description", help="目录说明"),
):
    """向 .specify/extension-catalogs.yml 添加目录。"""
    from .extensions import ExtensionCatalog, ValidationError

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]错误：[/red] 当前不是 spec-kit 项目（缺少 .specify/ 目录）")
        console.print("请在 spec-kit 项目根目录运行此命令")
        raise typer.Exit(1)

    # Validate URL
    tmp_catalog = ExtensionCatalog(project_root)
    try:
        tmp_catalog._validate_catalog_url(url)
    except ValidationError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    config_path = specify_dir / "extension-catalogs.yml"

    # Load existing config
    if config_path.exists():
        try:
            config = yaml.safe_load(config_path.read_text()) or {}
        except Exception as e:
            console.print(f"[red]错误：[/red] 读取 {config_path} 失败：{e}")
            raise typer.Exit(1)
    else:
        config = {}

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        console.print("[red]错误：[/red] 无效的目录配置：'catalogs' 必须是列表。")
        raise typer.Exit(1)

    # Check for duplicate name
    for existing in catalogs:
        if isinstance(existing, dict) and existing.get("name") == name:
            console.print(f"[yellow]警告：[/yellow] 已存在名为 '{name}' 的目录。")
            console.print("请先使用 'specify-zh extension catalog remove' 删除，或换一个名称。")
            raise typer.Exit(1)

    catalogs.append({
        "name": name,
        "url": url,
        "priority": priority,
        "install_allowed": install_allowed,
        "description": description,
    })

    config["catalogs"] = catalogs
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))

    install_label = "允许安装" if install_allowed else "仅发现"
    console.print(f"\n[green]✓[/green] 已添加目录 '[bold]{name}[/bold]'（{install_label}）")
    console.print(f"  URL：{url}")
    console.print(f"  优先级：{priority}")
    console.print(f"\n配置已保存到 {config_path.relative_to(project_root)}")


@catalog_app.command("remove")
def catalog_remove(
    name: str = typer.Argument(help="要移除的目录名称"),
):
    """从 .specify/extension-catalogs.yml 移除目录。"""
    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]错误：[/red] 当前不是 spec-kit 项目（缺少 .specify/ 目录）")
        console.print("请在 spec-kit 项目根目录运行此命令")
        raise typer.Exit(1)

    config_path = specify_dir / "extension-catalogs.yml"
    if not config_path.exists():
        console.print("[red]错误：[/red] 未找到目录配置，无可移除内容。")
        raise typer.Exit(1)

    try:
        config = yaml.safe_load(config_path.read_text()) or {}
    except Exception:
        console.print("[red]错误：[/red] 读取目录配置失败。")
        raise typer.Exit(1)

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        console.print("[red]错误：[/red] 无效的目录配置：'catalogs' 必须是列表。")
        raise typer.Exit(1)
    original_count = len(catalogs)
    catalogs = [c for c in catalogs if isinstance(c, dict) and c.get("name") != name]

    if len(catalogs) == original_count:
        console.print(f"[red]错误：[/red] 未找到目录 '{name}'。")
        raise typer.Exit(1)

    config["catalogs"] = catalogs
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))

    console.print(f"[green]✓[/green] 已移除目录 '{name}'")
    if not catalogs:
        console.print("\n[dim]配置中已无目录，将回退到内置默认值。[/dim]")


@extension_app.command("add")
def extension_add(
    extension: str = typer.Argument(help="扩展名称或路径"),
    dev: bool = typer.Option(False, "--dev", help="从本地目录安装"),
    from_url: Optional[str] = typer.Option(None, "--from", help="从自定义 URL 安装"),
):
    """安装扩展。"""
    from .extensions import ExtensionManager, ExtensionCatalog, ExtensionError, ValidationError, CompatibilityError

    project_root = Path.cwd()

    # Check if we're in a spec-kit project
    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]错误：[/red] 当前不是 spec-kit 项目（缺少 .specify/ 目录）")
        console.print("请在 spec-kit 项目根目录运行此命令")
        raise typer.Exit(1)

    manager = ExtensionManager(project_root)
    speckit_version = get_speckit_version()

    try:
        with console.status(f"[cyan]正在安装扩展：{extension}[/cyan]"):
            if dev:
                # Install from local directory
                source_path = Path(extension).expanduser().resolve()
                if not source_path.exists():
                    console.print(f"[red]错误：[/red] 未找到目录：{source_path}")
                    raise typer.Exit(1)

                if not (source_path / "extension.yml").exists():
                    console.print(f"[red]错误：[/red] 在 {source_path} 中未找到 extension.yml")
                    raise typer.Exit(1)

                manifest = manager.install_from_directory(source_path, speckit_version)

            elif from_url:
                # Install from URL (ZIP file)
                import urllib.request
                import urllib.error
                from urllib.parse import urlparse

                # Validate URL
                parsed = urlparse(from_url)
                is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")

                if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
                    console.print("[red]错误：[/red] 出于安全考虑，URL 必须使用 HTTPS。")
                    console.print("仅允许 localhost 使用 HTTP。")
                    raise typer.Exit(1)

                # Warn about untrusted sources
                console.print("[yellow]警告：[/yellow] 正在从外部 URL 安装扩展。")
                console.print("请仅安装来自可信来源的扩展。\n")
                console.print(f"正在从 {from_url} 下载...")

                # Download ZIP to temp location
                download_dir = project_root / ".specify" / "extensions" / ".cache" / "downloads"
                download_dir.mkdir(parents=True, exist_ok=True)
                zip_path = download_dir / f"{extension}-url-download.zip"

                try:
                    with urllib.request.urlopen(from_url, timeout=60) as response:
                        zip_data = response.read()
                    zip_path.write_bytes(zip_data)

                    # Install from downloaded ZIP
                    manifest = manager.install_from_zip(zip_path, speckit_version)
                except urllib.error.URLError as e:
                    console.print(f"[red]错误：[/red] 从 {from_url} 下载失败：{e}")
                    raise typer.Exit(1)
                finally:
                    # Clean up downloaded ZIP
                    if zip_path.exists():
                        zip_path.unlink()

            else:
                # Install from catalog
                catalog = ExtensionCatalog(project_root)

                # Check if extension exists in catalog
                ext_info = catalog.get_extension_info(extension)
                if not ext_info:
                    console.print(f"[red]错误：[/red] 在目录中未找到扩展 '{extension}'")
                    console.print("\n可先搜索可用扩展：")
                    console.print("  specify extension search")
                    raise typer.Exit(1)

                # Enforce install_allowed policy
                if not ext_info.get("_install_allowed", True):
                    catalog_name = ext_info.get("_catalog_name", "community")
                    console.print(
                        f"[red]Error:[/red] '{extension}' is available in the "
                        f"'{catalog_name}' 目录中存在该扩展，但当前不允许从该目录安装。"
                    )
                    console.print(
                        f"\n若要允许安装，请将 '{extension}' 加入已批准目录，"
                        f"并在 .specify/extension-catalogs.yml 中设置 install_allowed: true。"
                    )
                    raise typer.Exit(1)

                # Download extension ZIP
                console.print(f"正在下载 {ext_info['name']} v{ext_info.get('version', 'unknown')}...")
                zip_path = catalog.download_extension(extension)

                try:
                    # Install from downloaded ZIP
                    manifest = manager.install_from_zip(zip_path, speckit_version)
                finally:
                    # Clean up downloaded ZIP
                    if zip_path.exists():
                        zip_path.unlink()

        console.print("\n[green]✓[/green] 扩展安装成功！")
        console.print(f"\n[bold]{manifest.name}[/bold] (v{manifest.version})")
        console.print(f"  {manifest.description}")
        console.print("\n[bold cyan]提供的命令：[/bold cyan]")
        for cmd in manifest.commands:
            console.print(f"  • {cmd['name']} - {cmd.get('description', '')}")

        console.print("\n[yellow]⚠[/yellow]  该扩展可能还需要配置")
        console.print(f"   请检查：.specify/extensions/{manifest.id}/")

    except ValidationError as e:
        console.print(f"\n[red]验证错误：[/red] {e}")
        raise typer.Exit(1)
    except CompatibilityError as e:
        console.print(f"\n[red]兼容性错误：[/red] {e}")
        raise typer.Exit(1)
    except ExtensionError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)


@extension_app.command("remove")
def extension_remove(
    extension: str = typer.Argument(help="要移除的扩展 ID"),
    keep_config: bool = typer.Option(False, "--keep-config", help="保留配置文件"),
    force: bool = typer.Option(False, "--force", help="跳过确认"),
):
    """卸载扩展。"""
    from .extensions import ExtensionManager

    project_root = Path.cwd()

    # Check if we're in a spec-kit project
    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]错误：[/red] 当前不是 spec-kit 项目（缺少 .specify/ 目录）")
        console.print("请在 spec-kit 项目根目录运行此命令")
        raise typer.Exit(1)

    manager = ExtensionManager(project_root)

    # Check if extension is installed
    if not manager.registry.is_installed(extension):
        console.print(f"[red]错误：[/red] 扩展 '{extension}' 尚未安装")
        raise typer.Exit(1)

    # Get extension info
    ext_manifest = manager.get_extension(extension)
    if ext_manifest:
        ext_name = ext_manifest.name
        cmd_count = len(ext_manifest.commands)
    else:
        ext_name = extension
        cmd_count = 0

    # Confirm removal
    if not force:
        console.print("\n[yellow]⚠  此操作将移除：[/yellow]")
        console.print(f"   • AI agent 中的 {cmd_count} 个命令")
        console.print(f"   • 扩展目录：.specify/extensions/{extension}/")
        if not keep_config:
            console.print("   • 配置文件（会先备份）")
        console.print()

        confirm = typer.confirm("是否继续？")
        if not confirm:
            console.print("已取消")
            raise typer.Exit(0)

    # Remove extension
    success = manager.remove(extension, keep_config=keep_config)

    if success:
        console.print(f"\n[green]✓[/green] 扩展 '{ext_name}' 已成功移除")
        if keep_config:
            console.print(f"\n配置文件已保留在 .specify/extensions/{extension}/")
        else:
            console.print(f"\n配置文件已备份到 .specify/extensions/.backup/{extension}/")
        console.print(f"\n重新安装：specify-zh extension add {extension}")
    else:
        console.print("[red]错误：[/red] 扩展移除失败")
        raise typer.Exit(1)


@extension_app.command("search")
def extension_search(
    query: str = typer.Argument(None, help="搜索关键词（可选）"),
    tag: Optional[str] = typer.Option(None, "--tag", help="按标签筛选"),
    author: Optional[str] = typer.Option(None, "--author", help="按作者筛选"),
    verified: bool = typer.Option(False, "--verified", help="仅显示已验证扩展"),
):
    """在目录中搜索可用扩展。"""
    from .extensions import ExtensionCatalog, ExtensionError

    project_root = Path.cwd()

    # Check if we're in a spec-kit project
    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]错误：[/red] 当前不是 spec-kit 项目（缺少 .specify/ 目录）")
        console.print("请在 spec-kit 项目根目录运行此命令")
        raise typer.Exit(1)

    catalog = ExtensionCatalog(project_root)

    try:
        console.print("🔍 正在搜索扩展目录...")
        results = catalog.search(query=query, tag=tag, author=author, verified_only=verified)

        if not results:
            console.print("\n[yellow]没有找到符合条件的扩展[/yellow]")
            if query or tag or author or verified:
                console.print("\n可以尝试：")
                console.print("  • 使用更宽泛的搜索词")
                console.print("  • 去掉部分筛选条件")
                console.print("  • specify extension search（查看全部）")
            raise typer.Exit(0)

        console.print(f"\n[green]找到 {len(results)} 个扩展：[/green]\n")

        for ext in results:
            # Extension header
            verified_badge = " [green]✓ 已验证[/green]" if ext.get("verified") else ""
            console.print(f"[bold]{ext['name']}[/bold] (v{ext['version']}){verified_badge}")
            console.print(f"  {ext['description']}")

            # Metadata
            console.print(f"\n  [dim]作者：[/dim] {ext.get('author', 'Unknown')}")
            if ext.get('tags'):
                tags_str = ", ".join(ext['tags'])
                console.print(f"  [dim]标签：[/dim] {tags_str}")

            # Source catalog
            catalog_name = ext.get("_catalog_name", "")
            install_allowed = ext.get("_install_allowed", True)
            if catalog_name:
                if install_allowed:
                    console.print(f"  [dim]来源目录：[/dim] {catalog_name}")
                else:
                    console.print(f"  [dim]来源目录：[/dim] {catalog_name} [yellow]（仅发现，不可安装）[/yellow]")

            # Stats
            stats = []
            if ext.get('downloads') is not None:
                stats.append(f"下载量：{ext['downloads']:,}")
            if ext.get('stars') is not None:
                stats.append(f"Stars：{ext['stars']}")
            if stats:
                console.print(f"  [dim]{' | '.join(stats)}[/dim]")

            # Links
            if ext.get('repository'):
                console.print(f"  [dim]仓库：[/dim] {ext['repository']}")

            # Install command (show warning if not installable)
            if install_allowed:
                console.print(f"\n  [cyan]安装：[/cyan] specify-zh extension add {ext['id']}")
            else:
                console.print(f"\n  [yellow]⚠[/yellow]  当前不能直接从 '{catalog_name}' 安装。")
                console.print(
                    f"  可将其加入 install_allowed: true 的已批准目录，"
                    f"或通过 ZIP URL 安装：specify-zh extension add {ext['id']} --from <zip-url>"
                )
            console.print()

    except ExtensionError as e:
        console.print(f"\n[red]错误：[/red] {e}")
        console.print("\n提示：目录可能暂时不可用，请稍后重试。")
        raise typer.Exit(1)


@extension_app.command("信息")
def extension_info(
    extension: str = typer.Argument(help="扩展 ID 或名称"),
):
    """显示扩展的详细信息。"""
    from .extensions import ExtensionCatalog, ExtensionManager, ExtensionError

    project_root = Path.cwd()

    # Check if we're in a spec-kit project
    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]错误：[/red] 非 spec-kit 项目（未找到 .specify/ 目录）")
        console.print("请在 spec-kit 项目根目录下执行此命令")
        raise typer.Exit(1)

    catalog = ExtensionCatalog(project_root)
    manager = ExtensionManager(project_root)

    try:
        ext_info = catalog.get_extension_info(extension)

        if not ext_info:
            console.print(f"[red]错误：[/red] 在目录中未找到扩展 '{extension}'")
            console.print("\n可运行：specify-zh extension search")
            raise typer.Exit(1)

        # Header
        verified_badge = " [green]✓ 已验证[/green]" if ext_info.get("verified") else ""
        console.print(f"\n[bold]{ext_info['name']}[/bold] (v{ext_info['version']}){verified_badge}")
        console.print(f"ID: {ext_info['id']}")
        console.print()

        # Description
        console.print(f"{ext_info['description']}")
        console.print()

        # Author and License
        console.print(f"[dim]作者：[/dim] {ext_info.get('author', '未知')}")
        console.print(f"[dim]许可证：[/dim] {ext_info.get('license', '未知')}")

        # Source catalog
        if ext_info.get("_catalog_name"):
            install_allowed = ext_info.get("_install_allowed", True)
            install_note = "" if install_allowed else " [yellow](仅发现)[/yellow]"
            console.print(f"[dim]来源目录：[/dim] {ext_info['_catalog_name']}{install_note}")
        console.print()

        # Requirements
        if ext_info.get('requires'):
            console.print("[bold]依赖要求：[/bold]")
            reqs = ext_info['requires']
            if reqs.get('speckit_version'):
                console.print(f"  • Spec Kit: {reqs['speckit_version']}")
            if reqs.get('tools'):
                for tool in reqs['tools']:
                    tool_name = tool['name']
                    tool_version = tool.get('version', 'any')
                    required = " （必需）" if tool.get('required') else " （可选）"
                    console.print(f"  • {tool_name}: {tool_version}{required}")
            console.print()

        # Provides
        if ext_info.get('provides'):
            console.print("[bold]提供内容：[/bold]")
            provides = ext_info['provides']
            if provides.get('commands'):
                console.print(f"  • 命令：{provides['commands']}")
            if provides.get('hooks'):
                console.print(f"  • 钉子：{provides['hooks']}")
            console.print()

        # Tags
        if ext_info.get('tags'):
            tags_str = ", ".join(ext_info['tags'])
            console.print(f"[bold]标签：[/bold] {tags_str}")
            console.print()

        # Statistics
        stats = []
        if ext_info.get('downloads') is not None:
            stats.append(f"下载量：{ext_info['downloads']:,}")
        if ext_info.get('stars') is not None:
            stats.append(f"星标：{ext_info['stars']}")
        if stats:
            console.print(f"[bold]统计信息：[/bold] {' | '.join(stats)}")
            console.print()

        # Links
        console.print("[bold]链接：[/bold]")
        if ext_info.get('repository'):
            console.print(f"  • 仓库：{ext_info['repository']}")
        if ext_info.get('homepage'):
            console.print(f"  • 主页：{ext_info['homepage']}")
        if ext_info.get('documentation'):
            console.print(f"  • 文档：{ext_info['documentation']}")
        if ext_info.get('changelog'):
            console.print(f"  • 更新日志：{ext_info['changelog']}")
        console.print()

        # Installation status and command
        is_installed = manager.registry.is_installed(ext_info['id'])
        install_allowed = ext_info.get("_install_allowed", True)
        if is_installed:
            console.print("[green]✓ 已安装[/green]")
            console.print(f"\n如需卸载：specify-zh extension remove {ext_info['id']}")
        elif install_allowed:
            console.print("[yellow]未安装[/yellow]")
            console.print(f"\n[cyan]安装：[/cyan] specify-zh extension add {ext_info['id']}")
        else:
            catalog_name = ext_info.get("_catalog_name", "community")
            console.print("[yellow]未安装[/yellow]")
            console.print(
                f"\n[yellow]⚠[/yellow]  '{ext_info['id']}' 在 '{catalog_name}' 目录中可用，"
                f"但不在已批准目录中。将其加入 .specify/extension-catalogs.yml "
                f"并设置 install_allowed: true 即可安装。"
            )

    except ExtensionError as e:
        console.print(f"\n[red]错误：[/red] {e}")
        raise typer.Exit(1)


@extension_app.command("更新")
def extension_update(
    extension: str = typer.Argument(None, help="要更新的扩展 ID（或 all）"),
):
    """将扩展更新到最新版本。"""
    from .extensions import ExtensionManager, ExtensionCatalog, ExtensionError
    from packaging import version as pkg_version

    project_root = Path.cwd()

    # Check if we're in a spec-kit project
    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]错误：[/red] 非 spec-kit 项目（未找到 .specify/ 目录）")
        console.print("请在 spec-kit 项目根目录下执行此命令")
        raise typer.Exit(1)

    manager = ExtensionManager(project_root)
    catalog = ExtensionCatalog(project_root)

    try:
        # Get list of extensions to update
        if extension:
            # Update specific extension
            if not manager.registry.is_installed(extension):
                console.print(f"[red]Error:[/red] Extension '{extension}' is not installed")
                raise typer.Exit(1)
            extensions_to_update = [extension]
        else:
            # Update all extensions
            installed = manager.list_installed()
            extensions_to_update = [ext["id"] for ext in installed]

        if not extensions_to_update:
            console.print("[yellow]未安装任何扩展[/yellow]")
            raise typer.Exit(0)

        console.print("🔄 正在检查更新...\n")

        updates_available = []

        for ext_id in extensions_to_update:
            # Get installed version
            metadata = manager.registry.get(ext_id)
            installed_version = pkg_version.Version(metadata["version"])

            # Get catalog info
            ext_info = catalog.get_extension_info(ext_id)
            if not ext_info:
                console.print(f"⚠  {ext_id}：在目录中未找到（已跳过）")
                continue

            catalog_version = pkg_version.Version(ext_info["version"])

            if catalog_version > installed_version:
                updates_available.append(
                    {
                        "id": ext_id,
                        "installed": str(installed_version),
                        "available": str(catalog_version),
                        "download_url": ext_info.get("download_url"),
                    }
                )
            else:
                console.print(f"✓ {ext_id}：已是最新（v{installed_version}）")

        if not updates_available:
            console.print("\n[green]所有扩展均已是最新版本！[/green]")
            raise typer.Exit(0)

        # Show available updates
        console.print("\n[bold]有可用更新：[/bold]\n")
        for update in updates_available:
            console.print(
                f"  • {update['id']}: {update['installed']} → {update['available']}"
            )

        console.print()
        confirm = typer.confirm("是否更新这些扩展？")
        if not confirm:
            console.print("已取消")
            raise typer.Exit(0)

        # Perform updates
        console.print()
        for update in updates_available:
            ext_id = update["id"]
            console.print(f"📦 正在更新 {ext_id}...")

            # TODO: 实现从 URL 下载并重新安装
            # 目前仅显示提示信息
            console.print(
                "[yellow]提示：[/yellow] 自动更新功能尚未实现。"
                "请手动更新："
            )
            console.print(f"  specify-zh extension remove {ext_id} --keep-config")
            console.print(f"  specify-zh extension add {ext_id}")

        console.print(
            "\n[cyan]提示：[/cyan] 自动更新将在后续版本推出"
        )

    except ExtensionError as e:
        console.print(f"\n[red]错误：[/red] {e}")
        raise typer.Exit(1)


@extension_app.command("启用")
def extension_enable(
    extension: str = typer.Argument(help="要启用的扩展 ID"),
):
    """启用已禁用的扩展。"""
    from .extensions import ExtensionManager, HookExecutor

    project_root = Path.cwd()

    # Check if we're in a spec-kit project
    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]错误：[/red] 非 spec-kit 项目（未找到 .specify/ 目录）")
        console.print("请在 spec-kit 项目根目录下执行此命令")
        raise typer.Exit(1)

    manager = ExtensionManager(project_root)
    hook_executor = HookExecutor(project_root)

    if not manager.registry.is_installed(extension):
        console.print(f"[red]错误：[/red] 扩展 '{extension}' 未安装")
        raise typer.Exit(1)

    # Update registry
    metadata = manager.registry.get(extension)
    if metadata.get("enabled", True):
        console.print(f"[yellow]扩展 '{extension}' 已处于启用状态[/yellow]")
        raise typer.Exit(0)

    metadata["enabled"] = True
    manager.registry.add(extension, metadata)

    # Enable hooks in extensions.yml
    config = hook_executor.get_project_config()
    if "hooks" in config:
        for hook_name in config["hooks"]:
            for hook in config["hooks"][hook_name]:
                if hook.get("extension") == extension:
                    hook["enabled"] = True
        hook_executor.save_project_config(config)

    console.print(f"[green]✓[/green] 扩展 '{extension}' 已启用")


@extension_app.command("禁用")
def extension_disable(
    extension: str = typer.Argument(help="要禁用的扩展 ID"),
):
    """禁用扩展（不卸载）。"""
    from .extensions import ExtensionManager, HookExecutor

    project_root = Path.cwd()

    # Check if we're in a spec-kit project
    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]错误：[/red] 非 spec-kit 项目（未找到 .specify/ 目录）")
        console.print("请在 spec-kit 项目根目录下执行此命令")
        raise typer.Exit(1)

    manager = ExtensionManager(project_root)
    hook_executor = HookExecutor(project_root)

    if not manager.registry.is_installed(extension):
        console.print(f"[red]错误：[/red] 扩展 '{extension}' 未安装")
        raise typer.Exit(1)

    # Update registry
    metadata = manager.registry.get(extension)
    if not metadata.get("enabled", True):
        console.print(f"[yellow]扩展 '{extension}' 已处于禁用状态[/yellow]")
        raise typer.Exit(0)

    metadata["enabled"] = False
    manager.registry.add(extension, metadata)

    # Disable hooks in extensions.yml
    config = hook_executor.get_project_config()
    if "hooks" in config:
        for hook_name in config["hooks"]:
            for hook in config["hooks"][hook_name]:
                if hook.get("extension") == extension:
                    hook["enabled"] = False
        hook_executor.save_project_config(config)

    console.print(f"[green]✓[/green] 扩展 '{extension}' 已禁用")
    console.print("\n命令将不可用，钉子将不再执行。")
    console.print(f"重新启用：specify-zh extension enable {extension}")


def main():
    app()

if __name__ == "__main__":
    main()
