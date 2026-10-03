#!/usr/bin/env python3
# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
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

from __future__ import annotations

import json
import os
import platform
import shutil
import ssl
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
import typer
import yaml
from rich.align import Align
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    tomllib = None

from specify_cli.constants import (
    BRAND_DISPLAY,
    CMD_NAME,
    DIST_NAME,
    TAGLINE,
    UPSTREAM_REPO,
)
from specify_cli.codex_prompts import (
    DEFAULT_CODEX_PROMPTS_DIR as CODEX_GLOBAL_PROMPTS_DIR,
    codex_slash_command,
    normalize_speckit_name as _normalize_speckit_name,
    render_codex_prompt as _render_codex_prompt,
    sync_codex_prompts_from_templates,
)
from specify_cli.network import (
    FALLBACK_GITLAB_INSTALL_URL,
    FALLBACK_GITLAB_REPO_URL,
    PRESET_MIRRORS,
    _format_rate_limit_error,
    _github_auth_headers,
    _github_token,
    _parse_rate_limit_headers,
    client,
    resolve_mirror_url,
    ssl_context,
)
from specify_cli.agents import (
    AGENT_CONFIG,
    AGENT_SKILLS_DIR_OVERRIDES,
    AI_ASSISTANT_ALIASES,
    AI_ASSISTANT_HELP,
    CLAUDE_LOCAL_PATH,
    DEFAULT_SKILLS_DIR,
    SCRIPT_TYPE_CHOICES,
    SKILL_DESCRIPTIONS,
    TOML_AGENTS,
    _build_ai_assistant_help,
    _get_skills_dir,
)
from specify_cli.ui import (
    BANNER,
    BannerGroup,
    StepTracker,
    _get_cli_distribution_version,
    console,
    get_key,
    select_with_arrows,
    show_banner,
)
from specify_cli.git import (
    _doctor_install_hint,
    check_tool,
    handle_vscode_settings,
    init_git_repo,
    is_git_repo,
    merge_json_files,
    run_command,
)
from specify_cli.diagnostics import (
    _build_doctor_recommendations,
    _check_github_connectivity,
    _collect_doctor_diagnostics,
)
from specify_cli.templates import (
    BUNDLED_CORE_DIR,
    BUNDLED_DOCS_DIR,
    BUNDLED_TEMPLATES_DIR,
    CONVENTIONS_DIRNAME,
    _build_template_tree_from_source,
    _bundled_asset_root_from_package,
    _copy_tree_into_project,
    _get_command_templates_dir,
    _get_conventions_registry_path,
    _parse_markdown_command_template,
    _print_json_error,
    _render_agent_command,
    _repo_root_from_source,
    _validate_init_args,
    bootstrap_template_from_fallback_source,
    download_and_extract_template,
    download_template_from_github,
    ensure_coding_conventions_from_docs,
    ensure_codex_prompts_from_templates,
    ensure_constitution_from_template,
    ensure_executable_scripts,
    install_ai_skills,
)
from specify_cli.artifacts import artifact_app
from specify_cli.bundles import bundle_app
from specify_cli.events import event_app
from specify_cli.integrations import integration_app
from specify_cli.presets import preset_app
from specify_cli.selfs import self_app
from specify_cli.workflows import workflow_app

app = typer.Typer(
    name=CMD_NAME,
    help="specify-cli-zh 规范驱动开发项目设置工具",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)


@app.callback()
def callback(ctx: typer.Context):
    """Show banner when no subcommand is provided."""
    if (
        ctx.invoked_subcommand is None
        and "--help" not in sys.argv
        and "-h" not in sys.argv
    ):
        show_banner()
        console.print(Align.center("[dim]运行 'specify-zh --help' 查看使用说明[/dim]"))
        console.print()


@app.command()
def init(
    project_name: Optional[str] = typer.Argument(
        None, help="新项目目录名称（使用 --here 时可省略，也可用 '.' 表示当前目录）"
    ),
    ai_assistant: str = typer.Option(None, "--ai", help=AI_ASSISTANT_HELP),
    ai_commands_dir: str = typer.Option(
        None,
        "--ai-commands-dir",
        help="agent 命令文件目录（使用 --ai generic 时必填，例如 .myagent/commands/）",
    ),
    script_type: str = typer.Option(None, "--script", help="使用的脚本类型：sh 或 ps"),
    ignore_agent_tools: bool = typer.Option(
        False, "--ignore-agent-tools", help="跳过 Claude Code 等 AI 工具的检测"
    ),
    no_git: bool = typer.Option(False, "--no-git", help="跳过 git 仓库初始化"),
    here: bool = typer.Option(
        False, "--here", help="在当前目录初始化项目，而不是创建新目录"
    ),
    force: bool = typer.Option(
        False, "--force", help="搭配 --here 使用时强制合并/覆盖（跳过确认）"
    ),
    skip_tls: bool = typer.Option(
        False, "--skip-tls", help="跳过 SSL/TLS 校验（不推荐）"
    ),
    debug: bool = typer.Option(
        False, "--debug", help="显示网络与解压失败的详细诊断信息"
    ),
    github_token: str = typer.Option(
        None,
        "--github-token",
        help="用于 API 请求的 GitHub Token（也可通过 GH_TOKEN 或 GITHUB_TOKEN 设置）",
    ),
    ai_skills: bool = typer.Option(
        False, "--ai-skills", help="将 Prompt.MD 模板安装为 agent skills（需搭配 --ai）"
    ),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="纯离线模式：跳过外部网络请求，直接使用内置模板秒级构建项目",
    ),
    mirror: Optional[str] = typer.Option(
        None,
        "--mirror",
        help="国内 GitHub 镜像加速源（如 fastgit, ghproxy 或自定义代理 URL）",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="预览将要创建的文件清单，不执行实际写入"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="以 JSON 格式输出初始化结果，不显示交互式进度"
    ),
) -> None:
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
    project_name, ai_assistant, here = _validate_init_args(
        project_name=project_name,
        ai_assistant=ai_assistant,
        ai_commands_dir=ai_commands_dir,
        here=here,
        ai_skills=ai_skills,
        json_output=json_output,
    )

    if here:
        project_name = Path.cwd().name
        project_path = Path.cwd()

        target_spec_dir = project_path / ".specify"
        if target_spec_dir.exists():
            console.print(
                "[yellow]警告：[/yellow] 目标路径已存在 .specify/ 目录（项目可能已初始化）。"
            )
            if not force and not json_output:
                response = typer.confirm(
                    "检测到已初始化的项目，是否覆盖？", default=False
                )
                if not response:
                    console.print("[yellow]已取消操作[/yellow]")
                    raise typer.Exit(0)
        else:
            existing_items = list(project_path.iterdir())
            if existing_items:
                console.print(
                    f"[yellow]警告：[/yellow] 当前目录非空（{len(existing_items)} 个条目）"
                )
                console.print(
                    "[yellow]模板文件会与现有内容合并，并可能覆盖已有文件[/yellow]"
                )
                if force or json_output:
                    console.print(
                        "[cyan]已提供 --force 或 --json：跳过确认，直接继续合并[/cyan]"
                    )
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
                console.print(
                    "[yellow]警告：[/yellow] 目标路径已存在 .specify/ 目录（项目可能已初始化）。"
                )
                if not force and not json_output:
                    response = typer.confirm(
                        "检测到已初始化的项目，是否覆盖？", default=False
                    )
                    if not response:
                        console.print("[yellow]已取消操作[/yellow]")
                        raise typer.Exit(0)
            else:
                error_panel = Panel(
                    f"Directory '[cyan]{project_name}[/cyan]' already exists\n"
                    "请选择其他项目名称，或先移除现有目录。",
                    title="[red]目录冲突[/red]",
                    border_style="red",
                    padding=(1, 2),
                )
                console.print()
                console.print(error_panel)
                if json_output:
                    _print_json_error("目录冲突：已有同名非空目录")
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
            console.print(
                f"[red]错误：[/red] 无效的 AI 助手 '{ai_assistant}'。可选值：{', '.join(AGENT_CONFIG.keys())}"
            )
            raise typer.Exit(1)
        selected_ai = ai_assistant
    else:
        # Create options dict for selection (agent_key: display_name)
        ai_choices = {
            key: f"{config['name']} "
            + (
                "[dim](CLI 工具)[/dim]"
                if config.get("requires_cli")
                else "[dim](IDE 扩展)[/dim]"
            )
            for key, config in AGENT_CONFIG.items()
            if key != "generic"
        }
        ai_choices["generic"] = "Custom Agent [dim](自定义)[/dim]"
        selected_ai = select_with_arrows(ai_choices, "选择你的 AI 助手：", "copilot")

    # Validate --ai-commands-dir usage
    if selected_ai == "generic":
        if not ai_commands_dir:
            console.print(
                "[red]错误：[/red] 使用 --ai generic 时必须提供 --ai-commands-dir"
            )
            console.print(
                "[dim]Example: specify-zh init my-project --ai generic --ai-commands-dir .myagent/commands/[/dim]"
            )
            raise typer.Exit(1)
    elif ai_commands_dir:
        console.print(
            f"[red]Error:[/red] --ai-commands-dir can only be used with --ai generic (not '{selected_ai}')"
        )
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
                    padding=(1, 2),
                )
                console.print()
                console.print(error_panel)
                raise typer.Exit(1)

    if script_type:
        if script_type not in SCRIPT_TYPE_CHOICES:
            console.print(
                f"[red]错误：[/red] 无效的脚本类型 '{script_type}'。可选值：{', '.join(SCRIPT_TYPE_CHOICES.keys())}"
            )
            raise typer.Exit(1)
        selected_script = script_type
    else:
        default_script = "ps" if os.name == "nt" else "sh"

        if sys.stdin.isatty():
            selected_script = select_with_arrows(
                SCRIPT_TYPE_CHOICES, "选择脚本类型（或按 Enter）", default_script
            )
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
        ("codex-prompts", "补齐 Codex prompts"),
        ("chmod", "确保脚本可执行"),
        ("constitution", "初始化章程"),
        ("conventions", "初始化编码规范"),
    ]:
        tracker.add(key, label)
    if ai_skills:
        tracker.add("ai-skills", "安装 agent skills")
    for key, label in [
        ("cleanup", "清理临时文件"),
        ("git", "初始化 git 仓库"),
        ("final", "完成"),
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
            json_data = {
                "status": "dry-run",
                "project_path": str(project_path),
                "ai_assistant": selected_ai,
                "script_type": selected_script,
                "ai_skills": ai_skills,
                "init_git": not no_git and should_init_git,
            }
            sys.stdout.write(json.dumps(json_data, indent=2) + "\n")
        raise typer.Exit(0)

    with Live(
        tracker.render(), console=console, refresh_per_second=8, transient=True
    ) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        try:
            verify = not skip_tls
            local_ssl_context = ssl_context if verify else False
            local_client = httpx.Client(verify=local_ssl_context)

            download_and_extract_template(
                project_path,
                selected_ai,
                selected_script,
                here,
                verbose=False,
                tracker=tracker,
                client=local_client,
                debug=debug,
                github_token=github_token,
                offline=offline,
                mirror=mirror,
            )

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

            ensure_codex_prompts_from_templates(
                project_path, selected_ai, tracker=tracker
            )
            ensure_executable_scripts(project_path, tracker=tracker)

            ensure_constitution_from_template(project_path, tracker=tracker)
            ensure_coding_conventions_from_docs(project_path, tracker=tracker)

            if ai_skills:
                skills_ok = install_ai_skills(
                    project_path, selected_ai, tracker=tracker
                )

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
                        cmds_dir = (
                            project_path / agent_folder.rstrip("/") / commands_subdir
                        )
                        if cmds_dir.exists():
                            try:
                                shutil.rmtree(cmds_dir)
                            except OSError:
                                # Best-effort cleanup: skills are already installed,
                                # so leaving stale commands is non-fatal.
                                console.print(
                                    "[yellow]警告：无法删除已提取的命令目录[/yellow]"
                                )

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
                env_lines = [
                    f"{k.ljust(_label_width)} → [bright_black]{v}[/bright_black]"
                    for k, v in _env_pairs
                ]
                console.print(
                    Panel(
                        "\n".join(env_lines), title="调试环境", border_style="magenta"
                    )
                )
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
            f'[cyan]git commit -m "Initial commit"[/cyan]',
            title="[red]Git 初始化失败[/red]",
            border_style="red",
            padding=(1, 2),
        )
        console.print(git_error_panel)

    # Agent folder security notice
    agent_config = AGENT_CONFIG.get(selected_ai)
    if agent_config:
        agent_folder = (
            ai_commands_dir if selected_ai == "generic" else agent_config["folder"]
        )
        if agent_folder:
            security_notice = Panel(
                f"部分 agents 可能会在项目内的 agent 目录中保存凭据、认证令牌或其他可识别的私密信息。\n"
                f"建议将 [cyan]{agent_folder}[/cyan]（或其中的敏感部分）加入 [cyan].gitignore[/cyan]，避免误提交凭据。",
                title="[yellow]Agent 目录安全提示[/yellow]",
                border_style="yellow",
                padding=(1, 2),
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
    if selected_ai == "codex" and not ai_skills:
        steps_lines.append(
            f"{step_num}. Codex prompts 已同步到 [cyan]{CODEX_GLOBAL_PROMPTS_DIR}[/cyan]，"
            "如当前会话未刷新，请重启 Codex 或重新打开工作区。"
        )
        step_num += 1

    if ai_skills:
        steps_lines.append(
            f"{step_num}. 开始使用已安装的 agent skills 与你的 AI 助手协作："
        )
        if selected_ai == "codex":
            steps_lines.append(
                "   2.1 使用 [cyan]speckit-constitution[/] skill 建立项目原则"
            )
            steps_lines.append(
                "   2.2 使用 [cyan]speckit-specify[/] skill 创建基础规范"
            )
            steps_lines.append("   2.3 使用 [cyan]speckit-plan[/] skill 生成实施计划")
            steps_lines.append(
                "   2.4 使用 [cyan]speckit-tasks[/] skill 生成可执行任务"
            )
            steps_lines.append("   2.5 使用 [cyan]speckit-implement[/] skill 执行实施")
            steps_lines.append(
                "   [dim]提示：在 Codex 中可直接点名 skill，例如“使用 speckit-constitution 这个 skill，……”[/dim]"
            )
        else:
            steps_lines.append(
                "   2.1 使用 [cyan]speckit-constitution[/] skill 建立项目原则"
            )
            steps_lines.append(
                "   2.2 使用 [cyan]speckit-specify[/] skill 创建基础规范"
            )
            steps_lines.append("   2.3 使用 [cyan]speckit-plan[/] skill 生成实施计划")
            steps_lines.append(
                "   2.4 使用 [cyan]speckit-tasks[/] skill 生成可执行任务"
            )
            steps_lines.append("   2.5 使用 [cyan]speckit-implement[/] skill 执行实施")
    else:
        steps_lines.append(f"{step_num}. 开始使用 slash commands 与你的 AI 助手协作：")
        if selected_ai == "codex":
            steps_lines.append(
                "   2.1 [cyan]/prompts:speckit-constitution[/] - 建立项目原则"
            )
            steps_lines.append(
                "   2.2 [cyan]/prompts:speckit-specify[/] - 创建基础规范"
            )
            steps_lines.append("   2.3 [cyan]/prompts:speckit-plan[/] - 生成实施计划")
            steps_lines.append(
                "   2.4 [cyan]/prompts:speckit-tasks[/] - 生成可执行任务"
            )
            steps_lines.append("   2.5 [cyan]/prompts:speckit-implement[/] - 执行实施")
        else:
            steps_lines.append("   2.1 [cyan]/speckit.constitution[/] - 建立项目原则")
            steps_lines.append("   2.2 [cyan]/speckit.specify[/] - 创建基础规范")
            steps_lines.append("   2.3 [cyan]/speckit.plan[/] - 生成实施计划")
            steps_lines.append("   2.4 [cyan]/speckit.tasks[/] - 生成可执行任务")
            steps_lines.append("   2.5 [cyan]/speckit.implement[/] - 执行实施")

    steps_panel = Panel(
        "\n".join(steps_lines), title="后续步骤", border_style="cyan", padding=(1, 2)
    )
    console.print()
    console.print(steps_panel)

    if ai_skills:
        enhancement_lines = [
            "这些是可选 skills，可用于提升规范质量与信心 [bright_black](improve quality & confidence)[/bright_black]",
            "",
            "○ [cyan]speckit-clarify[/] [bright_black](可选)[/bright_black] - 在规划前用结构化提问消除模糊点",
            "○ [cyan]speckit-analyze[/] [bright_black](可选)[/bright_black] - 生成跨制品一致性与对齐分析",
            "○ [cyan]speckit-checklist[/] [bright_black](可选)[/bright_black] - 生成质量检查清单，验证需求完整性、清晰度与一致性",
        ]
    else:
        if selected_ai == "codex":
            enhancement_lines = [
                "这些是可选命令，可用于提升规范质量与信心 [bright_black](improve quality & confidence)[/bright_black]",
                "",
                "○ [cyan]/prompts:speckit-clarify[/] [bright_black](可选)[/bright_black] - 在规划前用结构化提问消除模糊点（若使用，请在 [cyan]/prompts:speckit-plan[/] 前执行）",
                "○ [cyan]/prompts:speckit-analyze[/] [bright_black](可选)[/bright_black] - 生成跨制品一致性与对齐分析（在 [cyan]/prompts:speckit-tasks[/] 之后、[cyan]/prompts:speckit-implement[/] 之前执行）",
                "○ [cyan]/prompts:speckit-checklist[/] [bright_black](可选)[/bright_black] - 生成质量检查清单，验证需求完整性、清晰度与一致性（在 [cyan]/prompts:speckit-plan[/] 之后执行）",
            ]
        else:
            enhancement_lines = [
                "这些是可选命令，可用于提升规范质量与信心 [bright_black](improve quality & confidence)[/bright_black]",
                "",
                "○ [cyan]/speckit.clarify[/] [bright_black](可选)[/bright_black] - 在规划前用结构化提问消除模糊点（若使用，请在 [cyan]/speckit.plan[/] 前执行）",
                "○ [cyan]/speckit.analyze[/] [bright_black](可选)[/bright_black] - 生成跨制品一致性与对齐分析（在 [cyan]/speckit.tasks[/] 之后、[cyan]/speckit.implement[/] 之前执行）",
                "○ [cyan]/speckit.checklist[/] [bright_black](可选)[/bright_black] - 生成质量检查清单，验证需求完整性、清晰度与一致性（在 [cyan]/speckit.plan[/] 之后执行）",
            ]
    enhancements_panel = Panel(
        "\n".join(enhancement_lines),
        title="增强命令",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print()
    console.print(enhancements_panel)


@app.command()
def check() -> None:
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
    ide_agents = [
        k
        for k, v in AGENT_CONFIG.items()
        if not v.get("requires_cli") and k != "generic"
    ]

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
            padding=(1, 2),
        )
    )

    console.print("\n[bold green]specify-zh 已可使用！[/bold green]")

    if not git_ok:
        console.print("[dim]提示：安装 git 以启用仓库管理[/dim]")

    if missing_cli_count > 0:
        missing_names = [
            AGENT_CONFIG[k]["name"] for k in cli_agents if not agent_results.get(k)
        ]
        # Recommend top 3 popular CLI tools
        popular = ["Claude Code", "Cursor", "Gemini CLI"]
        recommend = [n for n in popular if n in missing_names]
        if recommend:
            console.print(
                f"[dim]提示：推荐优先安装 CLI 工具（如 {', '.join(recommend[:3])}）以获得最佳体验[/dim]"
            )
        elif not any(agent_results.values()):
            console.print("[dim]提示：安装 AI 助手可获得最佳体验[/dim]")


@app.command("codex-sync")
def codex_sync(
    project_path: Optional[Path] = typer.Option(
        None, "--project", "-p", help="要同步项目本地 prompts 的路径，默认当前目录"
    ),
    global_prompts_dir: Optional[Path] = typer.Option(
        None, "--global-dir", help="Codex 全局 prompts 目录，默认 ~/.codex/prompts"
    ),
    overwrite: bool = typer.Option(
        True,
        "--overwrite/--no-overwrite",
        help="是否更新已存在的 spec-kit Codex prompts",
    ),
):
    """同步 Codex slash commands，并显示可直接执行的命令。"""
    target_project = (project_path or Path.cwd()).resolve()
    if not target_project.exists():
        console.print(f"[red]错误：项目路径不存在：[/red] {target_project}")
        raise typer.Exit(1)

    templates_dir = _get_command_templates_dir()
    if templates_dir is None:
        console.print("[red]错误：未找到内置命令模板，无法同步 Codex prompts[/red]")
        raise typer.Exit(1)

    command_templates = sorted(templates_dir.glob("*.md"))
    if not command_templates:
        console.print("[red]错误：命令模板目录为空，无法同步 Codex prompts[/red]")
        raise typer.Exit(1)

    result = sync_codex_prompts_from_templates(
        command_templates,
        target_project,
        global_prompts_dir=global_prompts_dir or CODEX_GLOBAL_PROMPTS_DIR,
        overwrite=overwrite,
    )

    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column("项", style="cyan", justify="right")
    summary.add_column("值", style="white")
    summary.add_row("项目 prompts", str(result.project_prompts_dir))
    summary.add_row("全局 prompts", str(result.global_prompts_dir))
    summary.add_row("新增", str(result.created))
    summary.add_row("更新", str(result.updated))
    summary.add_row("保留", str(result.preserved))

    console.print(
        Panel(
            summary,
            title="[bold cyan]Codex prompts 已同步[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    preferred_order = [
        "constitution",
        "specify",
        "clarify",
        "plan",
        "tasks",
        "analyze",
        "checklist",
        "implement",
        "taskstoissues",
    ]
    order = {name: index for index, name in enumerate(preferred_order)}
    commands = sorted(
        result.command_names, key=lambda name: (order.get(name, 999), name)
    )

    command_table = Table(show_header=True, header_style="bold cyan")
    command_table.add_column("命令", style="green")
    command_table.add_column("说明")
    descriptions = {
        "constitution": "建立或校准项目原则",
        "specify": "明确需求与验收标准",
        "clarify": "澄清需求中的模糊点",
        "plan": "生成技术实施计划",
        "tasks": "生成可执行任务清单",
        "analyze": "做跨制品一致性分析",
        "checklist": "生成质量检查清单",
        "implement": "执行任务并实现功能",
        "taskstoissues": "将任务转换为 GitHub Issues",
    }
    for command in commands:
        command_table.add_row(
            codex_slash_command(command),
            descriptions.get(command, "Spec Kit 工作流命令"),
        )

    console.print()
    console.print(
        Panel(
            command_table,
            title="[bold green]Codex 中可直接执行[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(
        "[dim]如果 Codex 已经打开，请重启当前 Codex 会话后再使用这些命令。[/dim]"
    )


@app.command()
def doctor() -> None:
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
        tracker.complete(
            "agents", f"检测到 {diagnostics['available_agent_count']} 个可用 CLI"
        )
    else:
        tracker.skip("agents", "尚未检测到可用的 AI CLI")

    console.print(tracker.render())
    console.print()

    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column("项", style="cyan", justify="right")
    summary_table.add_column("值", style="white")
    summary_table.add_row("当前路径", str(diagnostics["path"]))
    summary_table.add_row(
        "分发包名",
        DIST_NAME
        if diagnostics["dist_ok"]
        else "[yellow]异常 (未找到安装记录)[/yellow]",
    )
    summary_table.add_row(
        "命令入口",
        diagnostics["cmd_path"]
        if diagnostics["cmd_path"]
        else "[yellow]异常 (不在 PATH 中)[/yellow]",
    )
    summary_table.add_row(
        "Spec Kit 项目", "是" if diagnostics["is_spec_project"] else "否"
    )
    summary_table.add_row("Git 仓库", "是" if diagnostics["is_git_repo"] else "否")
    summary_table.add_row(
        "GitHub Token", "已配置" if diagnostics["has_github_token"] else "未配置"
    )
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
            "\n".join(
                f"{idx}. {item}" for idx, item in enumerate(recommendations, start=1)
            ),
            title="[bold yellow]建议的下一步[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
    )

    if diagnostics["is_spec_project"]:
        follow_up = [
            "1. 若使用 Codex，请运行 `/prompts:speckit-constitution` 建立或校准项目原则",
            "2. 若使用其他 agent，请运行 `/speckit.constitution` 明确同一步骤",
            "3. 接着继续对应风格的 specify / plan 工作流",
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
def version() -> None:
    """显示版本与系统信息。"""
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
                    dt = datetime.fromisoformat(release_date.replace("Z", "+00:00"))
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
    info_table.add_row("可执行文件路径", cmd_path)
    info_table.add_row("CLI 版本", cli_version)
    info_table.add_row("运行模式", run_mode)
    info_table.add_row("", "")
    info_table.add_row("模板仓库", f"github/{repo_name}")
    info_table.add_row("模板版本", template_version)
    info_table.add_row("发布时间", release_date)
    info_table.add_row("", "")
    info_table.add_row("Python", platform.python_version())
    info_table.add_row("OpenSSL", getattr(ssl, "OPENSSL_VERSION", "unknown"))
    info_table.add_row("平台", platform.system())
    info_table.add_row("架构", platform.machine())
    info_table.add_row("系统版本", platform.version())

    panel = Panel(
        info_table,
        title="[bold cyan]specify-cli-zh 信息[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
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

app.add_typer(workflow_app, name="workflow")
app.add_typer(preset_app, name="preset")
app.add_typer(bundle_app, name="bundle")
app.add_typer(integration_app, name="integration")
app.add_typer(artifact_app, name="artifact")
app.add_typer(event_app, name="event")
app.add_typer(self_app, name="self")


def get_speckit_version() -> str:
    """Get current spec-kit version."""
    version, _ = _get_cli_distribution_version()
    return version


@extension_app.command("list")
def extension_list(
    available: bool = typer.Option(False, "--available", help="显示目录中可用的扩展"),
    all_extensions: bool = typer.Option(
        False, "--all", help="同时显示已安装和可用扩展"
    ),
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

            console.print(
                f"  [{status_color}]{status_icon}[/{status_color}] [bold]{ext['name']}[/bold] (v{ext['version']})"
            )
            console.print(f"     {ext['description']}")
            console.print(
                f"     命令数：{ext['command_count']} | Hooks：{ext['hook_count']} | 状态：{'已启用' if ext['enabled'] else '已禁用'}"
            )
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
            proj_loaded = (
                config_path.exists()
                and catalog._load_catalog_config(config_path) is not None
            )
        except ValidationError:
            proj_loaded = False
        if proj_loaded:
            console.print(
                f"[dim]配置文件：{config_path.relative_to(project_root)}[/dim]"
            )
        else:
            try:
                user_loaded = (
                    user_config_path.exists()
                    and catalog._load_catalog_config(user_config_path) is not None
                )
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
        False,
        "--install-allowed/--no-install-allowed",
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
            console.print(
                "请先使用 'specify-zh extension catalog remove' 删除，或换一个名称。"
            )
            raise typer.Exit(1)

    catalogs.append(
        {
            "name": name,
            "url": url,
            "priority": priority,
            "install_allowed": install_allowed,
            "description": description,
        }
    )

    config["catalogs"] = catalogs
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))

    install_label = "允许安装" if install_allowed else "仅发现"
    console.print(
        f"\n[green]✓[/green] 已添加目录 '[bold]{name}[/bold]'（{install_label}）"
    )
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
    from .extensions import (
        ExtensionManager,
        ExtensionCatalog,
        ExtensionError,
        ValidationError,
        CompatibilityError,
    )

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
                    console.print(
                        f"[red]错误：[/red] 在 {source_path} 中未找到 extension.yml"
                    )
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

                if parsed.scheme != "https" and not (
                    parsed.scheme == "http" and is_localhost
                ):
                    console.print(
                        "[red]错误：[/red] 出于安全考虑，URL 必须使用 HTTPS。"
                    )
                    console.print("仅允许 localhost 使用 HTTP。")
                    raise typer.Exit(1)

                # Warn about untrusted sources
                console.print("[yellow]警告：[/yellow] 正在从外部 URL 安装扩展。")
                console.print("请仅安装来自可信来源的扩展。\n")
                console.print(f"正在从 {from_url} 下载...")

                # Download ZIP to temp location
                download_dir = (
                    project_root / ".specify" / "extensions" / ".cache" / "downloads"
                )
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
                console.print(
                    f"正在下载 {ext_info['name']} v{ext_info.get('version', 'unknown')}..."
                )
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
            console.print(
                f"\n配置文件已备份到 .specify/extensions/.backup/{extension}/"
            )
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
        results = catalog.search(
            query=query, tag=tag, author=author, verified_only=verified
        )

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
            console.print(
                f"[bold]{ext['name']}[/bold] (v{ext['version']}){verified_badge}"
            )
            console.print(f"  {ext['description']}")

            # Metadata
            console.print(f"\n  [dim]作者：[/dim] {ext.get('author', 'Unknown')}")
            if ext.get("tags"):
                tags_str = ", ".join(ext["tags"])
                console.print(f"  [dim]标签：[/dim] {tags_str}")

            # Source catalog
            catalog_name = ext.get("_catalog_name", "")
            install_allowed = ext.get("_install_allowed", True)
            if catalog_name:
                if install_allowed:
                    console.print(f"  [dim]来源目录：[/dim] {catalog_name}")
                else:
                    console.print(
                        f"  [dim]来源目录：[/dim] {catalog_name} [yellow]（仅发现，不可安装）[/yellow]"
                    )

            # Stats
            stats = []
            if ext.get("downloads") is not None:
                stats.append(f"下载量：{ext['downloads']:,}")
            if ext.get("stars") is not None:
                stats.append(f"Stars：{ext['stars']}")
            if stats:
                console.print(f"  [dim]{' | '.join(stats)}[/dim]")

            # Links
            if ext.get("repository"):
                console.print(f"  [dim]仓库：[/dim] {ext['repository']}")

            # Install command (show warning if not installable)
            if install_allowed:
                console.print(
                    f"\n  [cyan]安装：[/cyan] specify-zh extension add {ext['id']}"
                )
            else:
                console.print(
                    f"\n  [yellow]⚠[/yellow]  当前不能直接从 '{catalog_name}' 安装。"
                )
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
        console.print(
            f"\n[bold]{ext_info['name']}[/bold] (v{ext_info['version']}){verified_badge}"
        )
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
            console.print(
                f"[dim]来源目录：[/dim] {ext_info['_catalog_name']}{install_note}"
            )
        console.print()

        # Requirements
        if ext_info.get("requires"):
            console.print("[bold]依赖要求：[/bold]")
            reqs = ext_info["requires"]
            if reqs.get("speckit_version"):
                console.print(f"  • Spec Kit: {reqs['speckit_version']}")
            if reqs.get("tools"):
                for tool in reqs["tools"]:
                    tool_name = tool["name"]
                    tool_version = tool.get("version", "any")
                    required = " （必需）" if tool.get("required") else " （可选）"
                    console.print(f"  • {tool_name}: {tool_version}{required}")
            console.print()

        # Provides
        if ext_info.get("provides"):
            console.print("[bold]提供内容：[/bold]")
            provides = ext_info["provides"]
            if provides.get("commands"):
                console.print(f"  • 命令：{provides['commands']}")
            if provides.get("hooks"):
                console.print(f"  • 钉子：{provides['hooks']}")
            console.print()

        # Tags
        if ext_info.get("tags"):
            tags_str = ", ".join(ext_info["tags"])
            console.print(f"[bold]标签：[/bold] {tags_str}")
            console.print()

        # Statistics
        stats = []
        if ext_info.get("downloads") is not None:
            stats.append(f"下载量：{ext_info['downloads']:,}")
        if ext_info.get("stars") is not None:
            stats.append(f"星标：{ext_info['stars']}")
        if stats:
            console.print(f"[bold]统计信息：[/bold] {' | '.join(stats)}")
            console.print()

        # Links
        console.print("[bold]链接：[/bold]")
        if ext_info.get("repository"):
            console.print(f"  • 仓库：{ext_info['repository']}")
        if ext_info.get("homepage"):
            console.print(f"  • 主页：{ext_info['homepage']}")
        if ext_info.get("documentation"):
            console.print(f"  • 文档：{ext_info['documentation']}")
        if ext_info.get("changelog"):
            console.print(f"  • 更新日志：{ext_info['changelog']}")
        console.print()

        # Installation status and command
        is_installed = manager.registry.is_installed(ext_info["id"])
        install_allowed = ext_info.get("_install_allowed", True)
        if is_installed:
            console.print("[green]✓ 已安装[/green]")
            console.print(f"\n如需卸载：specify-zh extension remove {ext_info['id']}")
        elif install_allowed:
            console.print("[yellow]未安装[/yellow]")
            console.print(
                f"\n[cyan]安装：[/cyan] specify-zh extension add {ext_info['id']}"
            )
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
                console.print(
                    f"[red]Error:[/red] Extension '{extension}' is not installed"
                )
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
            console.print("[yellow]提示：[/yellow] 自动更新功能尚未实现。请手动更新：")
            console.print(f"  specify-zh extension remove {ext_id} --keep-config")
            console.print(f"  specify-zh extension add {ext_id}")

        console.print("\n[cyan]提示：[/cyan] 自动更新将在后续版本推出")

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

__all__ = [
    "AGENT_CONFIG",
    "AGENT_SKILLS_DIR_OVERRIDES",
    "AI_ASSISTANT_ALIASES",
    "AI_ASSISTANT_HELP",
    "BANNER",
    "BRAND_DISPLAY",
    "BUNDLED_CORE_DIR",
    "BUNDLED_DOCS_DIR",
    "BUNDLED_TEMPLATES_DIR",
    "BannerGroup",
    "CLAUDE_LOCAL_PATH",
    "CMD_NAME",
    "CODEX_GLOBAL_PROMPTS_DIR",
    "CONVENTIONS_DIRNAME",
    "DEFAULT_SKILLS_DIR",
    "DIST_NAME",
    "FALLBACK_GITLAB_INSTALL_URL",
    "FALLBACK_GITLAB_REPO_URL",
    "PRESET_MIRRORS",
    "SCRIPT_TYPE_CHOICES",
    "SKILL_DESCRIPTIONS",
    "StepTracker",
    "TAGLINE",
    "TOML_AGENTS",
    "UPSTREAM_REPO",
    "_build_ai_assistant_help",
    "_build_doctor_recommendations",
    "_build_template_tree_from_source",
    "_bundled_asset_root_from_package",
    "_check_github_connectivity",
    "_collect_doctor_diagnostics",
    "_copy_tree_into_project",
    "_doctor_install_hint",
    "_format_rate_limit_error",
    "_get_cli_distribution_version",
    "_get_command_templates_dir",
    "_get_conventions_registry_path",
    "_get_skills_dir",
    "_github_auth_headers",
    "_github_token",
    "_normalize_speckit_name",
    "_parse_markdown_command_template",
    "_parse_rate_limit_headers",
    "_print_json_error",
    "_render_agent_command",
    "_render_codex_prompt",
    "_repo_root_from_source",
    "_validate_init_args",
    "app",
    "bootstrap_template_from_fallback_source",
    "callback",
    "catalog_add",
    "catalog_app",
    "catalog_list",
    "catalog_remove",
    "check",
    "check_tool",
    "client",
    "codex_slash_command",
    "codex_sync",
    "console",
    "doctor",
    "download_and_extract_template",
    "download_template_from_github",
    "ensure_codex_prompts_from_templates",
    "ensure_coding_conventions_from_docs",
    "ensure_constitution_from_template",
    "ensure_executable_scripts",
    "extension_add",
    "extension_app",
    "extension_disable",
    "extension_enable",
    "extension_info",
    "extension_list",
    "extension_remove",
    "extension_search",
    "extension_update",
    "get_key",
    "get_speckit_version",
    "handle_vscode_settings",
    "init",
    "init_git_repo",
    "install_ai_skills",
    "is_git_repo",
    "main",
    "merge_json_files",
    "resolve_mirror_url",
    "run_command",
    "select_with_arrows",
    "show_banner",
    "shutil",
    "ssl_context",
    "subprocess",
    "sync_codex_prompts_from_templates",
    "version",
    "workflow_app",
    "artifact_app",
    "bundle_app",
    "event_app",
    "integration_app",
    "preset_app",
    "self_app",
]
