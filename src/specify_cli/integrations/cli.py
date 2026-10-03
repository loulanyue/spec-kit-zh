# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""CLI commands for managing AI coding assistant integrations."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .manager import IntegrationManager

console = Console()
err_console = Console(stderr=True)

integration_app = typer.Typer(
    name="integration",
    help="管理 AI 编码助手集成 (GitHub Copilot, Claude Code, Trae, Qwen, Cursor 等)",
    add_completion=False,
)

catalog_app = typer.Typer(
    name="catalog",
    help="管理集成目录源",
    add_completion=False,
)
integration_app.add_typer(catalog_app, name="catalog")


@integration_app.command("list")
def integration_list(
    all_integrations: bool = typer.Option(
        False, "--all", "-a", help="显示所有支持的 AI 助手"
    ),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
) -> None:
    """列出当前项目激活的或所有支持的 AI 编码助手集成。"""
    mgr = IntegrationManager()
    active_keys = set(mgr.detect_active_integrations())
    all_agents = mgr.get_all_agents()

    if as_json:
        data = [
            {
                "key": k,
                "name": v.get("name"),
                "folder": v.get("folder"),
                "is_active": k in active_keys,
            }
            for k, v in all_agents.items()
            if all_integrations or (k in active_keys)
        ]
        console.print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(
        title="AI 助手集成列表" if all_integrations else "当前项目激活的 AI 助手",
        header_style="bold cyan",
    )
    table.add_column("集成 Key", style="bold green")
    table.add_column("AI 助手名称", style="white")
    table.add_column("项目配置目录", style="yellow")
    table.add_column("状态", style="magenta")

    for k, v in sorted(all_agents.items()):
        is_active = k in active_keys
        if not all_integrations and not is_active:
            continue
        status_str = (
            "[bold green]已激活 (Active)[/bold green]"
            if is_active
            else "[dim]未配置[/dim]"
        )
        table.add_row(k, v.get("name", k), v.get("folder", "N/A"), status_str)

    console.print(table)
    if not all_integrations and not active_keys:
        console.print(
            "\n[yellow]提示: 当前项目尚未检测到激活的 AI 助手配置目录。[/yellow]\n"
            "[dim]运行 'specify-zh integration list --all' 查看所有支持的助手，或使用 'specify-zh integration switch <key>' 激活。[/dim]"
        )


@integration_app.command("info")
def integration_info(
    integration_key: str = typer.Argument(
        ..., help="AI 助手 Key (如 claude, copilot, trae, qwen)"
    ),
) -> None:
    """查看指定 AI 助手的集成配置规范与要求。"""
    mgr = IntegrationManager()
    info = mgr.get_info(integration_key)
    if not info:
        err_console.print(f"[red]错误: 未知的 AI 助手 '{integration_key}'。[/red]")
        raise typer.Exit(1)

    info_text = (
        f"[bold]标识 Key:[/bold] {info['canonical_key']}\n"
        f"[bold]名称:[/bold] {info.get('name')}\n"
        f"[bold]配置目录:[/bold] {info.get('folder')}\n"
        f"[bold]指令存放子目录:[/bold] {info.get('commands_subdir', 'commands')}\n"
        f"[bold]是否需要 CLI 工具:[/bold] {'是' if info.get('requires_cli') else '否 (IDE内置)'}\n"
        f"[bold]官方安装地址:[/bold] {info.get('install_url') or 'IDE 内置扩展'}"
    )
    console.print(
        Panel(info_text, title=f"AI 集成详情: {info.get('name')}", border_style="cyan")
    )


@integration_app.command("switch")
def integration_switch(
    target_key: str = typer.Argument(..., help="要切换至的目标 AI 助手 Key"),
    skills: bool = typer.Option(
        True, "--skills/--no-skills", help="是否同时安装 Agent Skills"
    ),
) -> None:
    """将项目的主要 AI 助手切换至指定目标，并初始化指令与技能模板。"""
    mgr = IntegrationManager()
    try:
        mgr.switch(target_key, enable_skills=skills)
        console.print(f"[green]✓ 成功将项目 AI 助手切换至 '{target_key}'！[/green]")
    except Exception as e:
        err_console.print(f"[red]切换失败: {e}[/red]")
        raise typer.Exit(1)


@integration_app.command("upgrade")
def integration_upgrade() -> None:
    """刷新并升级当前项目已激活的所有 AI 助手的指令与技能模板。"""
    mgr = IntegrationManager()
    active = mgr.detect_active_integrations()
    if not active:
        console.print("[dim]当前项目未检测到激活的 AI 助手。[/dim]")
        return

    for key in active:
        try:
            mgr.switch(key)
            console.print(f"[green]✓ 已成功刷新 '{key}' 助手模板与技能[/green]")
        except Exception as e:
            err_console.print(f"[red]刷新 '{key}' 失败: {e}[/red]")


@catalog_app.command("list")
def integration_catalog_list() -> None:
    """列出集成目录源。"""
    console.print(
        Panel(
            "内置官方 AI 助手支持库（含 Copilot, Claude, Gemini, Trae, Qwen, Cursor 等 30+ 助手）",
            title="集成目录源 (Integration Catalogs)",
            border_style="cyan",
        )
    )
