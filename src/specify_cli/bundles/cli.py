# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""CLI commands for managing spec-kit bundles."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .catalog import BundleCatalog
from .manager import BundleManager

console = Console()
err_console = Console(stderr=True)

bundle_app = typer.Typer(
    name="bundle",
    help="管理 Spec Kit 组合包 (Bundle: 扩展 + 工作流的场景化套件)",
    add_completion=False,
)


@bundle_app.command("list")
def bundle_list(
    available: bool = typer.Option(
        False, "--available", "-a", help="显示目录中可用的所有组合包"
    ),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
) -> None:
    """列出已安装或可用的组合包。"""
    mgr = BundleManager()
    cat = BundleCatalog()

    if available:
        bundles = cat.list_available()
        if as_json:
            console.print(
                json.dumps([b.__dict__ for b in bundles], indent=2, ensure_ascii=False)
            )
            return

        table = Table(title="Spec Kit 可用组合包列表", header_style="bold cyan")
        table.add_column("Bundle ID", style="bold green")
        table.add_column("名称", style="white")
        table.add_column("版本", style="yellow")
        table.add_column("角色/受众", style="cyan")
        table.add_column("包含组件", style="magenta")
        table.add_column("描述", style="dim")

        for b in bundles:
            components_str = (
                f"{b.provides_extensions} 扩展, {b.provides_workflows} 工作流"
            )
            table.add_row(
                b.id,
                b.name,
                b.version,
                b.role,
                components_str,
                b.description,
            )
        console.print(table)
    else:
        installed = mgr.list_installed()
        if as_json:
            console.print(
                json.dumps(
                    [
                        {
                            "id": b.id,
                            "name": b.name,
                            "version": b.version,
                            "role": b.role,
                            "extensions": [e.id for e in b.provides_extensions],
                            "workflows": [w.id for w in b.provides_workflows],
                            "description": b.description,
                        }
                        for b in installed
                    ],
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return

        if not installed:
            console.print(
                "[dim]当前项目未安装任何组合包。运行 'specify-zh bundle list --available' 查看可用组合包。[/dim]"
            )
            return

        table = Table(title="已安装的组合包", header_style="bold cyan")
        table.add_column("Bundle ID", style="bold green")
        table.add_column("名称", style="white")
        table.add_column("版本", style="yellow")
        table.add_column("角色", style="cyan")
        table.add_column("包含扩展", style="magenta")
        table.add_column("包含工作流", style="blue")

        for b in installed:
            exts_str = ", ".join(e.id for e in b.provides_extensions) or "无"
            wfs_str = ", ".join(w.id for w in b.provides_workflows) or "无"
            table.add_row(b.id, b.name, b.version, b.role, exts_str, wfs_str)
        console.print(table)


@bundle_app.command("search")
def bundle_search(
    query: str = typer.Argument(..., help="搜索关键词（ID、名称、描述或标签）"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
) -> None:
    """在组合包目录中搜索。"""
    cat = BundleCatalog()
    results = cat.search(query)

    if as_json:
        console.print(
            json.dumps([b.__dict__ for b in results], indent=2, ensure_ascii=False)
        )
        return

    if not results:
        console.print(f"[yellow]未找到匹配 '{query}' 的组合包。[/yellow]")
        return

    table = Table(title=f"搜索结果: '{query}'", header_style="bold cyan")
    table.add_column("Bundle ID", style="bold green")
    table.add_column("名称", style="white")
    table.add_column("版本", style="yellow")
    table.add_column("描述", style="dim")
    table.add_column("标签", style="blue")

    for b in results:
        table.add_row(b.id, b.name, b.version, b.description, ", ".join(b.tags))
    console.print(table)


@bundle_app.command("info")
def bundle_info(
    bundle_id: str = typer.Argument(..., help="Bundle ID"),
) -> None:
    """查看指定组合包的详情与包含的扩展和工作流。"""
    mgr = BundleManager()
    cat = BundleCatalog()

    manifest = mgr.get_installed(bundle_id) or cat.get_bundled_manifest(bundle_id)
    if not manifest:
        entry = cat.get_info(bundle_id)
        if not entry:
            err_console.print(f"[red]错误: 未找到组合包 '{bundle_id}'。[/red]")
            raise typer.Exit(1)

        info_text = (
            f"[bold]ID:[/bold] {entry.id}\n"
            f"[bold]名称:[/bold] {entry.name}\n"
            f"[bold]版本:[/bold] {entry.version}\n"
            f"[bold]角色:[/bold] {entry.role}\n"
            f"[bold]作者:[/bold] {entry.author}\n"
            f"[bold]描述:[/bold] {entry.description}\n"
            f"[bold]标签:[/bold] {', '.join(entry.tags)}\n"
            f"[bold]包含:[/bold] {entry.provides_extensions} 个扩展, {entry.provides_workflows} 个工作流"
        )
        console.print(
            Panel(info_text, title=f"组合包详情: {entry.name}", border_style="cyan")
        )
        return

    exts_info = (
        "\n".join(f"  • {e.id} (v{e.version})" for e in manifest.provides_extensions)
        or "  无"
    )
    wfs_info = (
        "\n".join(f"  • {w.id} (v{w.version})" for w in manifest.provides_workflows)
        or "  无"
    )

    info_text = (
        f"[bold]ID:[/bold] {manifest.id}\n"
        f"[bold]名称:[/bold] {manifest.name}\n"
        f"[bold]版本:[/bold] {manifest.version}\n"
        f"[bold]角色:[/bold] {manifest.role}\n"
        f"[bold]作者:[/bold] {manifest.author}\n"
        f"[bold]许可证:[/bold] {manifest.license}\n"
        f"[bold]描述:[/bold] {manifest.description}\n"
        f"[bold]标签:[/bold] {', '.join(manifest.tags)}\n\n"
        f"[bold green]包含扩展 (Extensions):[/bold green]\n{exts_info}\n\n"
        f"[bold blue]包含工作流 (Workflows):[/bold blue]\n{wfs_info}"
    )
    console.print(
        Panel(info_text, title=f"组合包详情: {manifest.name}", border_style="cyan")
    )


@bundle_app.command("install")
def bundle_install(
    bundle_id: str = typer.Argument(
        ..., help="要安装的 Bundle ID（如 bugfix、assess）"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="强制覆盖已安装的组合包"),
) -> None:
    """安装指定组合包（自动编排安装其包含的扩展与工作流流水线）。"""
    mgr = BundleManager()
    try:
        manifest = mgr.install(bundle_id, force=force)
        console.print(
            f"[green]✓ 成功安装组合包 '{manifest.name}' (v{manifest.version})[/green]"
        )
        if manifest.provides_extensions:
            console.print(
                f"  [dim]• 已关联激活扩展: {', '.join(e.id for e in manifest.provides_extensions)}[/dim]"
            )
        if manifest.provides_workflows:
            console.print(
                f"  [dim]• 已关联注册工作流: {', '.join(w.id for w in manifest.provides_workflows)}[/dim]"
            )
    except Exception as e:
        err_console.print(f"[red]安装组合包失败: {e}[/red]")
        raise typer.Exit(1)


@bundle_app.command("add", hidden=True)
def bundle_add(
    bundle_id: str = typer.Argument(..., help="Bundle ID"),
    force: bool = typer.Option(False, "--force", "-f", help="强制覆盖"),
) -> None:
    """bundle install 的同义命令。"""
    bundle_install(bundle_id, force=force)


@bundle_app.command("remove")
def bundle_remove(
    bundle_id: str = typer.Argument(..., help="要卸载的 Bundle ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="跳过确认直接卸载"),
) -> None:
    """从当前项目卸载指定组合包（及其关联组件）。"""
    mgr = BundleManager()
    if not yes:
        confirm = typer.confirm(
            f"确定要卸载组合包 '{bundle_id}' 及其关联的扩展与工作流吗？"
        )
        if not confirm:
            console.print("[dim]已取消操作。[/dim]")
            return

    if mgr.remove(bundle_id):
        console.print(f"[green]✓ 成功卸载组合包 '{bundle_id}'[/green]")
    else:
        err_console.print(f"[yellow]未找到已安装的组合包 '{bundle_id}'[/yellow]")
        raise typer.Exit(1)
