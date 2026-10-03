# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""CLI commands for specify-zh self management."""

from __future__ import annotations

import json

import typer
from packaging import version as pkg_version
from rich.console import Console
from rich.panel import Panel

from .upgrade import check_latest_version, upgrade_in_place

console = Console()
err_console = Console(stderr=True)

self_app = typer.Typer(
    name="self",
    help="管理 specify-zh CLI 自身（检查新版本、在线自升级）",
    add_completion=False,
)


def _get_current_version() -> str:
    try:
        from specify_cli import get_speckit_version

        return get_speckit_version()
    except Exception:
        return "0.9.6"


@self_app.command("check")
def self_check(
    mirror: str = typer.Option(None, "--mirror", "-m", help="使用的镜像代理"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
) -> None:
    """检查 specify-zh CLI 是否有可用的更新版本。"""
    current = _get_current_version()
    console.print(f"[dim]正在查询最新版本 (当前版本: {current})...[/dim]")
    latest, source = check_latest_version(mirror=mirror)

    has_update = False
    if latest:
        try:
            has_update = pkg_version.parse(latest) > pkg_version.parse(current)
        except Exception:
            has_update = latest != current

    if as_json:
        console.print(
            json.dumps(
                {
                    "current_version": current,
                    "latest_version": latest,
                    "has_update": has_update,
                    "source": source,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if not latest:
        console.print("[yellow]未能连接到版本服务器获取最新发布信息。[/yellow]")
        return

    if has_update:
        console.print(
            Panel(
                f"[bold green]发现新版本可用！[/bold green]\n\n"
                f"• 当前版本: [yellow]{current}[/yellow]\n"
                f"• 最新版本: [green]{latest}[/green] (来源: {source})\n\n"
                f"运行 [bold cyan]specify-zh self upgrade[/bold cyan] 即可就地升级。",
                title="版本检查提示",
                border_style="green",
            )
        )
    else:
        console.print(f"[green]✓ 您当前使用的已是最新版本 (v{current})。[/green]")


@self_app.command("upgrade")
def self_upgrade(
    dry_run: bool = typer.Option(False, "--dry-run", help="预览升级操作但不实际执行"),
    mirror: str = typer.Option(
        None, "--mirror", "-m", help="指定国内 pip / 下载镜像源"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="跳过确认直接升级"),
) -> None:
    """就地升级 specify-zh 命令行工具至最新版本。"""
    current = _get_current_version()
    if not yes and not dry_run:
        confirm = typer.confirm(f"确定要检查并升级 specify-zh (当前 v{current}) 吗？")
        if not confirm:
            console.print("[dim]已取消升级。[/dim]")
            return

    console.print("[cyan]正在执行升级任务...[/cyan]")
    success, msg = upgrade_in_place(dry_run=dry_run, mirror=mirror)
    if success:
        console.print(f"[green]✓ {msg}[/green]")
    else:
        err_console.print(f"[red]{msg}[/red]")
        raise typer.Exit(1)
