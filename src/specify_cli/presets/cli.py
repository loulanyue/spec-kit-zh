# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""CLI commands for managing spec-kit presets."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .catalog import PresetCatalog
from .manager import PresetManager
from .resolver import PresetResolver

console = Console()
err_console = Console(stderr=True)

preset_app = typer.Typer(
    name="preset",
    help="管理 Spec Kit 预设（模板与指令重载包）",
    add_completion=False,
)

catalog_app = typer.Typer(
    name="catalog",
    help="管理预设目录源",
    add_completion=False,
)
preset_app.add_typer(catalog_app, name="catalog")


@preset_app.command("list")
def preset_list(
    available: bool = typer.Option(
        False, "--available", "-a", help="显示目录中所有可用的预设"
    ),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
) -> None:
    """列出已安装或可用的预设。"""
    mgr = PresetManager()
    cat = PresetCatalog()

    if available:
        presets = cat.list_available()
        if as_json:
            console.print(
                json.dumps([p.__dict__ for p in presets], indent=2, ensure_ascii=False)
            )
            return

        table = Table(title="Spec Kit 可用预设列表", header_style="bold cyan")
        table.add_column("预设 ID", style="bold green")
        table.add_column("名称", style="white")
        table.add_column("版本", style="yellow")
        table.add_column("描述", style="dim")
        table.add_column("类型", style="magenta")

        for p in presets:
            table.add_row(
                p.id,
                p.name,
                p.version,
                p.description,
                "内置 (Bundled)" if p.bundled else "社区 (Community)",
            )
        console.print(table)
    else:
        installed = mgr.list_installed()
        if as_json:
            console.print(
                json.dumps(
                    [
                        {
                            "id": p.id,
                            "name": p.name,
                            "version": p.version,
                            "description": p.description,
                            "tags": p.tags,
                        }
                        for p in installed
                    ],
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return

        if not installed:
            console.print(
                "[dim]当前项目未安装任何预设。运行 'specify-zh preset list --available' 查看可用预设。[/dim]"
            )
            return

        table = Table(title="已安装的预设", header_style="bold cyan")
        table.add_column("预设 ID", style="bold green")
        table.add_column("名称", style="white")
        table.add_column("版本", style="yellow")
        table.add_column("指令数", style="cyan")
        table.add_column("模板数", style="magenta")
        table.add_column("描述", style="dim")

        for p in installed:
            table.add_row(
                p.id,
                p.name,
                p.version,
                str(len(p.provides_commands)),
                str(len(p.provides_templates)),
                p.description,
            )
        console.print(table)


@preset_app.command("search")
def preset_search(
    query: str = typer.Argument(..., help="搜索关键词（ID、名称、描述或标签）"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
) -> None:
    """在预设目录中搜索。"""
    cat = PresetCatalog()
    results = cat.search(query)

    if as_json:
        console.print(
            json.dumps([p.__dict__ for p in results], indent=2, ensure_ascii=False)
        )
        return

    if not results:
        console.print(f"[yellow]未找到匹配 '{query}' 的预设。[/yellow]")
        return

    table = Table(title=f"搜索结果: '{query}'", header_style="bold cyan")
    table.add_column("预设 ID", style="bold green")
    table.add_column("名称", style="white")
    table.add_column("版本", style="yellow")
    table.add_column("描述", style="dim")
    table.add_column("标签", style="blue")

    for p in results:
        table.add_row(p.id, p.name, p.version, p.description, ", ".join(p.tags))
    console.print(table)


@preset_app.command("info")
def preset_info(
    preset_id: str = typer.Argument(..., help="预设 ID"),
) -> None:
    """查看指定预设的详细信息与提供内容。"""
    mgr = PresetManager()
    cat = PresetCatalog()

    manifest = mgr.get_installed(preset_id) or cat.get_bundled_manifest(preset_id)
    if not manifest:
        entry = cat.get_info(preset_id)
        if not entry:
            err_console.print(f"[red]错误: 未找到预设 '{preset_id}'。[/red]")
            raise typer.Exit(1)

        info_text = (
            f"[bold]ID:[/bold] {entry.id}\n"
            f"[bold]名称:[/bold] {entry.name}\n"
            f"[bold]版本:[/bold] {entry.version}\n"
            f"[bold]作者:[/bold] {entry.author}\n"
            f"[bold]描述:[/bold] {entry.description}\n"
            f"[bold]标签:[/bold] {', '.join(entry.tags)}\n"
            f"[bold]类型:[/bold] {'内置' if entry.bundled else '社区'}"
        )
        console.print(
            Panel(info_text, title=f"预设详情: {entry.name}", border_style="cyan")
        )
        return

    info_text = (
        f"[bold]ID:[/bold] {manifest.id}\n"
        f"[bold]名称:[/bold] {manifest.name}\n"
        f"[bold]版本:[/bold] {manifest.version}\n"
        f"[bold]作者:[/bold] {manifest.author}\n"
        f"[bold]许可证:[/bold] {manifest.license}\n"
        f"[bold]依赖 spec-kit:[/bold] {manifest.requires_speckit or '无特定限制'}\n"
        f"[bold]描述:[/bold] {manifest.description}\n"
        f"[bold]标签:[/bold] {', '.join(manifest.tags)}\n\n"
        f"[bold green]提供的指令重载 ({len(manifest.provides_commands)}):[/bold green]\n"
        + (
            "\n".join(
                f"  • {c.name} -> {c.file} ({c.strategy})"
                for c in manifest.provides_commands
            )
            or "  无"
        )
        + f"\n\n[bold magenta]提供的模板 ({len(manifest.provides_templates)}):[/bold magenta]\n"
        + (
            "\n".join(
                f"  • {t.name} -> {t.file} ({t.strategy})"
                for t in manifest.provides_templates
            )
            or "  无"
        )
    )
    console.print(
        Panel(info_text, title=f"预设详情: {manifest.name}", border_style="cyan")
    )


@preset_app.command("add")
def preset_add(
    preset_id: str = typer.Argument(..., help="预设 ID 或本地预设目录"),
    priority: int = typer.Option(
        10, "--priority", "-p", help="生效优先级（数值越小优先级越高）"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="若已存在强制覆盖"),
    dev: bool = typer.Option(False, "--dev", help="从本地目录开发模式安装"),
) -> None:
    """安装指定预设到当前项目中 (.specify/presets/)。"""
    mgr = PresetManager()
    try:
        dev_path = Path(preset_id).resolve() if dev else None
        target_id = dev_path.name if dev and dev_path else preset_id
        manifest = mgr.install(
            target_id, priority=priority, force=force, dev_path=dev_path
        )
        console.print(
            f"[green]✓ 成功安装预设 '{manifest.name}' (v{manifest.version}, 优先级 {priority})[/green]"
        )
    except Exception as e:
        err_console.print(f"[red]安装失败: {e}[/red]")
        raise typer.Exit(1)


@preset_app.command("remove")
def preset_remove(
    preset_id: str = typer.Argument(..., help="要卸载的预设 ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="跳过确认直接卸载"),
) -> None:
    """从当前项目卸载预设。"""
    mgr = PresetManager()
    if not yes:
        confirm = typer.confirm(f"确定要卸载预设 '{preset_id}' 吗？")
        if not confirm:
            console.print("[dim]已取消操作。[/dim]")
            return

    if mgr.remove(preset_id):
        console.print(f"[green]✓ 成功卸载预设 '{preset_id}'[/green]")
    else:
        err_console.print(f"[yellow]未找到已安装的预设 '{preset_id}'[/yellow]")
        raise typer.Exit(1)


@preset_app.command("update")
def preset_update(
    preset_id: str = typer.Argument(None, help="要更新的预设 ID"),
    all_presets: bool = typer.Option(False, "--all", "-a", help="更新所有已安装的预设"),
) -> None:
    """更新已安装的预设至最新版本。"""
    mgr = PresetManager()
    if all_presets:
        installed = mgr.list_installed()
        if not installed:
            console.print("[dim]没有已安装的预设需要更新。[/dim]")
            return
        for p in installed:
            try:
                mgr.update(p.id)
                console.print(f"[green]✓ 成功更新预设 '{p.id}'[/green]")
            except Exception as e:
                err_console.print(f"[red]更新预设 '{p.id}' 失败: {e}[/red]")
    elif preset_id:
        try:
            manifest = mgr.update(preset_id)
            console.print(f"[green]✓ 成功更新预设 '{manifest.name}' 至最新版本[/green]")
        except Exception as e:
            err_console.print(f"[red]更新失败: {e}[/red]")
            raise typer.Exit(1)
    else:
        console.print("[yellow]请提供预设 ID 或指定 --all 参数。[/yellow]")


@preset_app.command("resolve")
def preset_resolve(
    template_name: str = typer.Argument(
        ..., help="模板名称（如 spec-template、plan-template）"
    ),
) -> None:
    """解析并展示指定模板在当前项目优先级栈中的最终生效路径。"""
    resolver = PresetResolver()
    path = resolver.resolve_template(template_name)
    if path:
        console.print(f"[green]解析成功:[/green] {path}")
    else:
        err_console.print(f"[red]未能解析模板 '{template_name}'[/red]")
        raise typer.Exit(1)


@catalog_app.command("list")
def preset_catalog_list() -> None:
    """列出已配置的预设目录源。"""
    cat = PresetCatalog()
    bundled_status = "[green]可用[/green]" if cat.bundled_dir else "[red]未找到[/red]"
    console.print(
        Panel(
            f"[bold]内置预设源:[/bold] {bundled_status} ({cat.bundled_dir or 'N/A'})\n"
            f"[bold]社区预设源:[/bold] GitHub spec-kit 官方社区源 (catalog.community.json)",
            title="预设目录源 (Preset Catalogs)",
            border_style="cyan",
        )
    )
