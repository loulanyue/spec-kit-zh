# spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`.
"""CLI commands for lifecycle events and hooks."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .dispatcher import EventDispatcher

console = Console()
err_console = Console(stderr=True)

event_app = typer.Typer(
    name="event",
    help="管理与触发 Spec Kit 生命周期事件钩子 (Event Hooks)",
    add_completion=False,
)


@event_app.command("list")
def event_list(
    as_json: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
) -> None:
    """列出当前项目注册的所有生命周期事件钩子。"""
    dispatcher = EventDispatcher()
    hooks = dispatcher.discover_hooks()

    if as_json:
        data = [
            {
                "event": h.event_name,
                "source": h.source,
                "script": str(h.script_path),
                "description": h.description,
            }
            for h in hooks
        ]
        console.print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="已注册的生命周期事件钩子", header_style="bold cyan")
    table.add_column("事件名称 (Event)", style="bold green")
    table.add_column("来源", style="magenta")
    table.add_column("脚本文件", style="white")
    table.add_column("说明", style="dim")

    for h in hooks:
        table.add_row(h.event_name, h.source, str(h.script_path.name), h.description)

    console.print(table)
    if not hooks:
        console.print(
            "\n[dim]当前未检测到任何事件钩子。您可以在 .specify/hooks/<event-name>.sh 放置自定义钩子脚本。[/dim]"
        )


@event_app.command("run")
def event_run(
    event_name: str = typer.Argument(
        ..., help="要触发的事件名称 (如 pre-specify, post-implement)"
    ),
    payload: str = typer.Option(
        "", "--payload", "-p", help="传入钩子标准输入 (stdin) 的数据"
    ),
    timeout: int = typer.Option(
        60, "--timeout", "-t", help="单个钩子执行超时时间 (秒)"
    ),
) -> None:
    """触发指定生命周期事件，顺序执行所有注册的钩子脚本。"""
    dispatcher = EventDispatcher()
    hooks = dispatcher.discover_hooks(event_name)

    if not hooks:
        console.print(
            f"[yellow]未找到针对事件 '{event_name}' 注册的任何钩子。[/yellow]"
        )
        return

    console.print(f"[cyan]正在分发事件: '{event_name}' ({len(hooks)} 个钩子)...[/cyan]")
    results = dispatcher.run_event(event_name, payload=payload, timeout=timeout)

    all_success = True
    for hook, code, output in results:
        status_color = "green" if code == 0 else "red"
        console.print(
            f"  • [{status_color}]退出码 {code}[/{status_color}] 来自 {hook.source} ({hook.script_path.name})"
        )
        if output:
            console.print(
                Panel(output, title=f"{hook.script_path.name} 输出", border_style="dim")
            )
        if code != 0:
            all_success = False

    if not all_success:
        err_console.print(f"\n[red]事件 '{event_name}' 部分钩子执行失败。[/red]")
        raise typer.Exit(1)
    else:
        console.print(f"\n[green]✓ 事件 '{event_name}' 所有钩子执行成功。[/green]")


@event_app.command("test")
def event_test(
    event_name: str = typer.Argument(..., help="要测试的事件名称"),
) -> None:
    """测试指定事件的钩子是否可正常发现和执行。"""
    event_run(event_name=event_name, payload="TEST_EVENT_PAYLOAD", timeout=10)
