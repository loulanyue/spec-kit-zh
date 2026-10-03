"""CLI interface for Spec Kit Workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry
from specify_cli.workflows.engine import WorkflowEngine
from specify_cli.workflows.models import RunStatus

console = Console()

workflow_app = typer.Typer(
    name="workflow",
    help="管理与运行 Spec-Driven Development 工作流自动化流水线",
    add_completion=False,
)

catalog_app = typer.Typer(
    name="catalog",
    help="管理工作流目录源",
    add_completion=False,
)
workflow_app.add_typer(catalog_app, name="catalog")


def _parse_inputs(inputs_list: list[str] | None) -> dict[str, str]:
    """Parse list of 'key=value' into a dictionary."""
    result: dict[str, str] = {}
    if not inputs_list:
        return result

    for item in inputs_list:
        if "=" in item:
            k, v = item.split("=", 1)
            result[k.strip()] = v.strip()
        else:
            result[item.strip()] = "true"
    return result


@workflow_app.command("list")
def workflow_list(
    available: bool = typer.Option(False, "--available", help="显示目录中可用的工作流"),
    all_workflows: bool = typer.Option(
        False, "--all", help="同时显示已安装和可用工作流"
    ),
):
    """列出工作流（默认显示已安装工作流）。"""
    project_root = Path.cwd()
    registry = WorkflowRegistry(project_root)
    installed = registry.list_installed()

    if not installed and not (available or all_workflows):
        console.print("[yellow]当前未安装任何自定义工作流。[/yellow]")
        console.print("\n可使用以下命令查看或安装内置/社区工作流：")
        console.print("  specify-zh workflow list --available")
        console.print("  specify-zh workflow add speckit")
        return

    if installed:
        table = Table(title="已安装工作流 (Installed Workflows)", border_style="cyan")
        table.add_column("工作流 ID", style="bold green")
        table.add_column("名称", style="cyan")
        table.add_column("版本", style="dim")
        table.add_column("步骤数", justify="right")
        table.add_column("说明")

        for wf in installed:
            table.add_row(
                wf.id, wf.name, f"v{wf.version}", str(len(wf.steps)), wf.description
            )

        console.print(table)
        console.print()

    if available or all_workflows:
        catalog = WorkflowCatalog(project_root)
        available_wfs = catalog.get_all_workflows()

        table = Table(title="可用工作流目录 (Available Workflows)", border_style="blue")
        table.add_column("工作流 ID", style="bold yellow")
        table.add_column("名称", style="cyan")
        table.add_column("版本", style="dim")
        table.add_column("来源目录")
        table.add_column("说明")

        for wf in available_wfs:
            table.add_row(
                wf.id, wf.name, f"v{wf.version}", wf.catalog_name, wf.description
            )

        console.print(table)
        console.print(
            "\n安装命令：[cyan]specify-zh workflow add <workflow-id>[/cyan]\n"
        )


@workflow_app.command("search")
def workflow_search(
    query: str = typer.Argument("", help="搜索关键词（工作流 ID、名称、标签或描述）"),
):
    """搜索工作流目录。"""
    catalog = WorkflowCatalog()
    matches = catalog.search(query)

    if not matches:
        console.print(f"[yellow]未找到与 '{query}' 匹配的工作流。[/yellow]")
        return

    table = Table(title=f"工作流搜索结果: '{query}'", border_style="blue")
    table.add_column("工作流 ID", style="bold yellow")
    table.add_column("名称", style="cyan")
    table.add_column("版本", style="dim")
    table.add_column("标签", style="magenta")
    table.add_column("说明")

    for wf in matches:
        tags_str = ", ".join(wf.tags) if wf.tags else "-"
        table.add_row(wf.id, wf.name, f"v{wf.version}", tags_str, wf.description)

    console.print(table)


@workflow_app.command("info")
def workflow_info(
    workflow_ref: str = typer.Argument(..., help="工作流 ID 或 YAML 文件路径"),
):
    """查看指定工作流的详细结构、输入参数与执行步骤。"""
    engine = WorkflowEngine()
    try:
        wf = engine.load_workflow(workflow_ref)
    except Exception as e:
        console.print(f"[red]错误：[/red] 无法加载工作流 '{workflow_ref}': {e}")
        raise typer.Exit(1)

    info_table = Table(show_header=False, box=None)
    info_table.add_column("属性", style="bold cyan", width=14)
    info_table.add_column("值")

    info_table.add_row("工作流 ID", wf.id)
    info_table.add_row("名称", wf.name)
    info_table.add_row("版本", wf.version)
    info_table.add_row("作者", wf.author or "-")
    info_table.add_row("说明", wf.description or "-")
    if wf.path:
        info_table.add_row("文件路径", str(wf.path))

    panel = Panel(
        info_table, title=f"[bold]工作流详情: {wf.name}[/bold]", border_style="cyan"
    )
    console.print(panel)

    if wf.inputs:
        console.print("\n[bold cyan]输入参数 (Inputs)：[/bold cyan]")
        in_table = Table(border_style="dim")
        in_table.add_column("参数名", style="bold yellow")
        in_table.add_column("类型", style="green")
        in_table.add_column("必填", justify="center")
        in_table.add_column("默认值", style="dim")
        in_table.add_column("提示说明")

        for name, in_def in wf.inputs.items():
            req_str = "[red]是[/red]" if in_def.required else "[dim]否[/dim]"
            def_str = str(in_def.default) if in_def.default is not None else "-"
            in_table.add_row(name, in_def.type, req_str, def_str, in_def.prompt or "-")
        console.print(in_table)

    if wf.steps:
        console.print("\n[bold cyan]执行步骤流水线 (Steps)：[/bold cyan]")
        step_table = Table(border_style="dim")
        step_table.add_column("序号", justify="right", width=4)
        step_table.add_column("步骤 ID", style="bold")
        step_table.add_column("类型", style="magenta")
        step_table.add_column("指令/命令/详情")

        for idx, step in enumerate(wf.steps, 1):
            detail = (
                step.command
                or step.run
                or step.prompt
                or step.message
                or step.name
                or "-"
            )
            step_table.add_row(str(idx), step.id, step.type, detail)
        console.print(step_table)
    console.print()


@workflow_app.command("add")
def workflow_add(
    workflow_id: str = typer.Argument(..., help="要安装的工作流 ID 或 URL"),
    mirror: Optional[str] = typer.Option(
        None,
        "--mirror",
        help="GitHub 加速镜像源 (如 fastgit, ghproxy, cf 或自定义 URL)",
    ),
):
    """安装指定工作流至本地项目 (.specify/workflows/)。"""
    project_root = Path.cwd()
    registry = WorkflowRegistry(project_root, mirror=mirror)
    try:
        wf = registry.install(workflow_id)
        console.print(
            f"[bold green]✔ 成功安装工作流：[/bold green] [bold]{wf.name}[/bold] ({wf.id} v{wf.version})"
        )
        console.print(f"配置文件保存在: .specify/workflows/{wf.id}/workflow.yml")
    except Exception as e:
        console.print(f"[red]安装失败：[/red] {e}")
        raise typer.Exit(1)


@workflow_app.command("remove")
def workflow_remove(
    workflow_id: str = typer.Argument(..., help="要卸载的工作流 ID"),
):
    """从本地项目卸载指定工作流。"""
    project_root = Path.cwd()
    registry = WorkflowRegistry(project_root)
    if registry.uninstall(workflow_id):
        console.print(f"[bold green]✔ 成功卸载工作流：[/bold green] {workflow_id}")
    else:
        console.print(f"[yellow]未找到已安装的工作流：[/yellow] {workflow_id}")
        raise typer.Exit(1)


@workflow_app.command("run")
def workflow_run(
    workflow_ref: str = typer.Argument(..., help="工作流 ID 或 YAML 路径"),
    inputs: list[str] = typer.Option(
        None, "--input", "-i", help="工作流输入参数 (格式: key=value，支持多次传递)"
    ),
    integration: Optional[str] = typer.Option(
        None,
        "--integration",
        help="指定执行 AI 助手集成（如 claude, copilot, qwen, trae 等）",
    ),
    auto_approve: bool = typer.Option(
        False, "--auto-approve", "-y", help="自动批准所有人工审查节点 (Gate Steps)"
    ),
    mirror: Optional[str] = typer.Option(None, "--mirror", help="加速镜像源"),
):
    """运行指定的工作流自动化流水线。"""
    engine = WorkflowEngine(mirror=mirror)
    try:
        wf = engine.load_workflow(workflow_ref)
    except Exception as e:
        console.print(f"[red]错误：[/red] 无法加载工作流 '{workflow_ref}': {e}")
        raise typer.Exit(1)

    parsed_inputs = _parse_inputs(inputs)
    if integration:
        parsed_inputs["integration"] = integration

    try:
        run_state = engine.create_run(wf, parsed_inputs)
    except ValueError as e:
        console.print(f"[red]参数错误：[/red] {e}")
        raise typer.Exit(1)

    console.print(
        f"[bold cyan]▶ 开始执行工作流：[/bold cyan] [bold]{wf.name}[/bold] (Run ID: [yellow]{run_state.run_id}[/yellow])\n"
    )
    final_state = engine.execute(
        run_state, wf, interactive=True, auto_approve=auto_approve
    )

    if final_state.status == RunStatus.COMPLETED:
        console.print(
            f"\n[bold green]✔ 运行完成！Run ID: {final_state.run_id}[/bold green]"
        )
    elif final_state.status == RunStatus.PAUSED:
        console.print(
            f"\n[bold yellow]⏸ 工作流已暂停。可使用以下命令恢复运行：[/bold yellow]\n"
            f"  specify-zh workflow resume {final_state.run_id}"
        )
    else:
        console.print(
            f"\n[bold red]✖ 工作流执行结束，状态: {final_state.status}[/bold red]"
        )
        raise typer.Exit(1)


@workflow_app.command("status")
def workflow_status(
    run_id: Optional[str] = typer.Argument(
        None, help="指定工作流 Run ID（不提供则列出所有历史运行）"
    ),
):
    """查看工作流运行状态。"""
    engine = WorkflowEngine()

    if run_id:
        run = engine.get_run(run_id)
        if not run:
            console.print(f"[red]未找到 Run ID：[/red] {run_id}")
            raise typer.Exit(1)

        table = Table(show_header=False, box=None)
        table.add_column("属性", style="bold cyan", width=14)
        table.add_column("值")

        table.add_row("Run ID", run.run_id)
        table.add_row("工作流 ID", run.workflow_id)
        status_color = (
            "green"
            if run.status == RunStatus.COMPLETED
            else ("yellow" if run.status == RunStatus.PAUSED else "red")
        )
        table.add_row("状态", f"[{status_color}]{run.status}[/{status_color}]")
        table.add_row("当前步骤序号", str(run.current_step_index))
        table.add_row("创建时间", run.created_at)
        table.add_row("最后更新", run.updated_at)

        console.print(
            Panel(table, title=f"Run 详情: {run.run_id}", border_style="cyan")
        )

        if run.step_results:
            console.print("\n[bold]各步骤执行结果：[/bold]")
            step_table = Table(border_style="dim")
            step_table.add_column("步骤 ID", style="bold")
            step_table.add_column("状态")
            step_table.add_column("输出摘要")

            for sid, sres in run.step_results.items():
                s_color = (
                    "green"
                    if sres.status == "COMPLETED"
                    else ("yellow" if sres.status == "PAUSED" else "red")
                )
                out_summary = str(sres.output) if sres.output else (sres.error or "-")
                if len(out_summary) > 60:
                    out_summary = out_summary[:57] + "..."
                step_table.add_row(
                    sid, f"[{s_color}]{sres.status}[/{s_color}]", out_summary
                )
            console.print(step_table)
        return

    # List all runs
    runs = engine.list_runs()
    if not runs:
        console.print("[yellow]当前没有任何工作流运行记录。[/yellow]")
        return

    table = Table(title="工作流历史运行记录 (Workflow Runs)", border_style="cyan")
    table.add_column("Run ID", style="bold yellow")
    table.add_column("工作流 ID", style="cyan")
    table.add_column("状态")
    table.add_column("已完成步骤", justify="right")
    table.add_column("创建时间", style="dim")

    for r in runs:
        s_color = (
            "green"
            if r.status == RunStatus.COMPLETED
            else ("yellow" if r.status == RunStatus.PAUSED else "red")
        )
        table.add_row(
            r.run_id,
            r.workflow_id,
            f"[{s_color}]{r.status}[/{s_color}]",
            str(len(r.step_results)),
            r.created_at[:19].replace("T", " "),
        )

    console.print(table)


@workflow_app.command("resume")
def workflow_resume(
    run_id: str = typer.Argument(..., help="要恢复的 Run ID"),
    choice: Optional[str] = typer.Option(
        None,
        "--choice",
        "-c",
        help="如果暂停在审查节点，直接提供审查选项（如 approve 或 reject）",
    ),
    auto_approve: bool = typer.Option(
        False, "--auto-approve", "-y", help="自动批准后续审查节点"
    ),
):
    """恢复暂停或失败的工作流运行。"""
    engine = WorkflowEngine()
    try:
        final_state = engine.resume(run_id, choice=choice, auto_approve=auto_approve)
    except Exception as e:
        console.print(f"[red]恢复运行失败：[/red] {e}")
        raise typer.Exit(1)

    if final_state.status == RunStatus.COMPLETED:
        console.print(
            f"\n[bold green]✔ 工作流已恢复并完成！Run ID: {final_state.run_id}[/bold green]"
        )
    elif final_state.status == RunStatus.PAUSED:
        console.print(
            f"\n[bold yellow]⏸ 工作流再次暂停。Run ID: {final_state.run_id}[/bold yellow]"
        )
    else:
        console.print(
            f"\n[bold red]✖ 工作流执行终止，状态: {final_state.status}[/bold red]"
        )
        raise typer.Exit(1)


# ===== Catalog Sub-Commands =====


@catalog_app.command("list")
def catalog_list():
    """列出当前激活的工作流目录源。"""
    catalog = WorkflowCatalog()
    catalogs = catalog.get_active_catalogs()

    table = Table(title="激活的工作流目录 (Active Catalogs)", border_style="blue")
    table.add_column("优先级", justify="right", width=6)
    table.add_column("名称", style="bold cyan")
    table.add_column("允许安装", justify="center")
    table.add_column("URL")
    table.add_column("说明")

    for cat in catalogs:
        allow_str = "[green]✔[/green]" if cat.install_allowed else "[dim]仅浏览[/dim]"
        table.add_row(str(cat.priority), cat.name, allow_str, cat.url, cat.description)

    console.print(table)


@catalog_app.command("add")
def catalog_add(
    url: str = typer.Argument(..., help="目录 URL (HTTPS)"),
    name: Optional[str] = typer.Option(None, "--name", help="目录名称标识"),
    priority: int = typer.Option(10, "--priority", help="目录优先级"),
):
    """添加自定义工作流目录源至项目配置 (.specify/workflow-catalogs.yml)。"""
    proj_dir = Path.cwd() / ".specify"
    proj_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = proj_dir / "workflow-catalogs.yml"

    data: dict = {"catalogs": []}
    if cfg_file.exists():
        try:
            data = yaml.safe_load(cfg_file.read_text(encoding="utf-8")) or {
                "catalogs": []
            }
        except Exception:
            data = {"catalogs": []}

    cats = data.get("catalogs", [])
    entry_name = name or f"custom-{len(cats) + 1}"
    cats.append(
        {
            "name": entry_name,
            "url": url,
            "priority": priority,
            "install_allowed": True,
        }
    )
    data["catalogs"] = cats

    cfg_file.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    console.print(f"[bold green]✔ 成功添加目录源：[/bold green] {entry_name} ({url})")


@catalog_app.command("remove")
def catalog_remove(
    index: int = typer.Argument(..., help="要移除的项目自定义目录索引 (从 1 开始)"),
):
    """从项目配置中移除指定索引的自定义工作流目录源。"""
    cfg_file = Path.cwd() / ".specify" / "workflow-catalogs.yml"
    if not cfg_file.exists():
        console.print("[yellow]当前项目不存在自定义工作流目录配置文件。[/yellow]")
        raise typer.Exit(1)

    try:
        data = yaml.safe_load(cfg_file.read_text(encoding="utf-8")) or {}
    except Exception:
        data = {}

    cats = data.get("catalogs", [])
    if index < 1 or index > len(cats):
        console.print(f"[red]无效的索引：[/red] {index} (当前共有 {len(cats)} 个目录)")
        raise typer.Exit(1)

    removed = cats.pop(index - 1)
    data["catalogs"] = cats
    cfg_file.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    console.print(
        f"[bold green]✔ 成功移除目录源：[/bold green] {removed.get('name', index)} ({removed.get('url')})"
    )


__all__ = ["catalog_app", "workflow_app"]
