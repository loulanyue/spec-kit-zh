# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""CLI commands for inspecting SDD artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .inspector import ArtifactInspector

console = Console()
err_console = Console(stderr=True)

artifact_app = typer.Typer(
    name="artifact",
    help="内省与审计 Spec-Driven Development 过程产物 (Spec, Plan, Tasks, Constitution)",
    add_completion=False,
)


@artifact_app.command("list")
def artifact_list(
    as_json: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
) -> None:
    """扫描并列出项目中的所有 SDD 文档构件。"""
    inspector = ArtifactInspector()
    items = inspector.list_artifacts()

    if as_json:
        data = [
            {
                "name": item.name,
                "type": item.artifact_type,
                "path": item.relative_path,
                "size_bytes": item.size_bytes,
                "modified": item.modified_time,
                "tasks_total": item.tasks_total,
                "tasks_completed": item.tasks_completed,
            }
            for item in items
        ]
        console.print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if not items:
        console.print(
            "[dim]当前项目未检测到任何 SDD 产物文档（如 spec.md, plan.md, tasks.md）。[/dim]"
        )
        return

    table = Table(title="项目 SDD 产物构件清单", header_style="bold cyan")
    table.add_column("构件类型", style="bold green")
    table.add_column("相对路径", style="white")
    table.add_column("大小", style="yellow")
    table.add_column("任务进度", style="magenta")
    table.add_column("修改时间", style="dim")

    for item in items:
        progress = (
            f"{item.tasks_completed}/{item.tasks_total}"
            if item.tasks_total > 0
            else "-"
        )
        table.add_row(
            item.artifact_type.upper(),
            item.relative_path,
            f"{item.size_bytes} B",
            progress,
            item.modified_time,
        )
    console.print(table)


@artifact_app.command("info")
def artifact_info(
    path: str = typer.Argument(..., help="构件文件的相对路径或名称"),
) -> None:
    """查看指定构件的详细结构与任务完成度。"""
    target = Path(path)
    if not target.is_file():
        # try find in project
        matches = list(Path.cwd().glob(f"**/{path}"))
        if matches:
            target = matches[0]
        else:
            err_console.print(f"[red]错误: 未找到文件 '{path}'。[/red]")
            raise typer.Exit(1)

    try:
        content = target.read_text(encoding="utf-8")
        lines = content.splitlines()
        headings = [line for line in lines if line.startswith("#")]
        inspector = ArtifactInspector()
        tot, comp = inspector._count_tasks(content)

        info_text = (
            f"[bold]路径:[/bold] {target.resolve()}\n"
            f"[bold]总行数:[/bold] {len(lines)}\n"
            f"[bold]总字符数:[/bold] {len(content)}\n"
            f"[bold]任务总数:[/bold] {tot} 项 (已完成: {comp}, 未完成: {tot - comp})\n\n"
            f"[bold cyan]文档章节大纲:[/bold cyan]\n"
            + ("\n".join(f"  {h}" for h in headings[:15]) or "  无标题")
        )
        if len(headings) > 15:
            info_text += f"\n  [dim]... 及其余 {len(headings) - 15} 个子章节[/dim]"

        console.print(
            Panel(info_text, title=f"构件详情: {target.name}", border_style="cyan")
        )
    except Exception as e:
        err_console.print(f"[red]读取文件失败: {e}[/red]")
        raise typer.Exit(1)


@artifact_app.command("inspect")
def artifact_inspect() -> None:
    """全面体检与审计项目所有构件的完整性与一致性。"""
    inspector = ArtifactInspector()
    items = inspector.list_artifacts()

    console.print(
        Panel("[bold]正在体检项目 SDD 产物完整性...[/bold]", border_style="cyan")
    )

    specs = [i for i in items if i.artifact_type == "spec"]
    plans = [i for i in items if i.artifact_type == "plan"]
    tasks = [i for i in items if i.artifact_type == "tasks"]
    constitutions = [i for i in items if i.artifact_type == "constitution"]

    console.print(f"• 找到 Specification 文档: [green]{len(specs)}[/green] 份")
    console.print(f"• 找到 Architecture Plan 文档: [green]{len(plans)}[/green] 份")
    console.print(f"• 找到 Implementation Tasks: [green]{len(tasks)}[/green] 份")
    console.print(f"• 找到 Constitution 规约: [green]{len(constitutions)}[/green] 份")

    uncompleted = sum(t.tasks_total - t.tasks_completed for t in tasks)
    if uncompleted > 0:
        console.print(
            f"\n[yellow]注意: 当前还有 {uncompleted} 个开发任务待执行完成。[/yellow]"
        )
    else:
        console.print(
            "\n[green]✓ 所有检测到的任务均已全部勾选完成或暂无未闭环任务。[/green]"
        )
