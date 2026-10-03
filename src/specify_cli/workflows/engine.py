"""Workflow execution engine, state machine, and runner."""

from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from specify_cli.workflows.catalog import (
    WorkflowCatalog,
    WorkflowRegistry,
    _find_bundled_workflows_dir,
)
from specify_cli.workflows.expressions import evaluate_condition, evaluate_expression
from specify_cli.workflows.models import (
    RunState,
    RunStatus,
    StepContext,
    StepResult,
    StepStatus,
    WorkflowDefinition,
    WorkflowStep,
)


class WorkflowEngine:
    """Core workflow execution engine."""

    def __init__(
        self,
        project_root: Path | None = None,
        console: Console | None = None,
        mirror: str | None = None,
    ):
        self.project_root = (project_root or Path.cwd()).resolve()
        self.console = console or Console()
        self.mirror = mirror
        self.runs_dir = self.project_root / ".specify" / "workflows" / "runs"
        self.registry = WorkflowRegistry(self.project_root, mirror=self.mirror)
        self.catalog = WorkflowCatalog(self.project_root, mirror=self.mirror)

    def load_workflow(self, workflow_ref: str | Path) -> WorkflowDefinition:
        """Load a workflow by path, installed ID, or bundled ID."""
        # 1. Direct path
        ref_path = Path(workflow_ref)
        if ref_path.is_file():
            return WorkflowDefinition.from_yaml(ref_path)

        if not ref_path.is_absolute():
            cand = self.project_root / ref_path
            if cand.is_file():
                return WorkflowDefinition.from_yaml(cand)

        ref_str = str(workflow_ref).strip()

        # 2. Installed in project
        installed = self.registry.get_installed(ref_str)
        if installed:
            return installed

        # 3. Bundled
        bundled_dir = _find_bundled_workflows_dir()
        if bundled_dir:
            wf_file = bundled_dir / ref_str / "workflow.yml"
            if wf_file.exists():
                return WorkflowDefinition.from_yaml(wf_file)
            wf_file = bundled_dir / ref_str / "workflow.yaml"
            if wf_file.exists():
                return WorkflowDefinition.from_yaml(wf_file)

        # 4. Catalog entry with auto-install
        entry = self.catalog.find_entry(ref_str)
        if entry:
            try:
                return self.registry.install(ref_str, self.catalog)
            except Exception:
                pass

        raise FileNotFoundError(
            f"Workflow '{workflow_ref}' not found locally or in catalogs."
        )

    def _resolve_inputs(
        self, workflow: WorkflowDefinition, cli_inputs: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate and coerce inputs against workflow definition schema."""
        resolved: dict[str, Any] = {}

        for name, in_def in workflow.inputs.items():
            raw_val = cli_inputs.get(name)

            if raw_val is None:
                if in_def.default is not None:
                    raw_val = in_def.default
                elif in_def.required:
                    prompt_msg = in_def.prompt or f"Please provide input for '{name}'"
                    raise ValueError(
                        f"Missing required workflow input: '{name}' ({prompt_msg})"
                    )
                else:
                    raw_val = None

            # Coerce value
            if raw_val is not None:
                t = in_def.type.lower()
                if t == "number":
                    try:
                        num = float(raw_val)
                        raw_val = int(num) if num.is_integer() else num
                    except (ValueError, TypeError):
                        raise ValueError(
                            f"Input '{name}' must be a number, got '{raw_val}'"
                        )
                elif t == "boolean":
                    if isinstance(raw_val, bool):
                        pass
                    elif isinstance(raw_val, str):
                        s = raw_val.strip().lower()
                        if s in ("true", "1", "yes", "y"):
                            raw_val = True
                        elif s in ("false", "0", "no", "n"):
                            raw_val = False
                        else:
                            raise ValueError(
                                f"Input '{name}' must be a boolean (true/false), got '{raw_val}'"
                            )
                    else:
                        raw_val = bool(raw_val)
                elif t == "string":
                    raw_val = str(raw_val)

                if in_def.enum and raw_val not in in_def.enum:
                    raise ValueError(
                        f"Input '{name}' must be one of {in_def.enum}, got '{raw_val}'"
                    )

            resolved[name] = raw_val

        # Copy extra inputs passed
        for k, v in cli_inputs.items():
            if k not in resolved:
                resolved[k] = v

        return resolved

    def create_run(
        self,
        workflow: WorkflowDefinition,
        inputs: dict[str, Any],
        run_id: str | None = None,
    ) -> RunState:
        """Create and initialize a new workflow run."""
        run_id = run_id or uuid.uuid4().hex[:8]
        resolved_inputs = self._resolve_inputs(workflow, inputs)

        wf_dir_str = ""
        if workflow.path:
            wf_dir_str = str(workflow.path.parent.resolve())

        run_state = RunState(
            run_id=run_id,
            workflow_id=workflow.id,
            status=RunStatus.CREATED,
            inputs=resolved_inputs,
            workflow_dir=wf_dir_str,
        )

        run_dir = self.runs_dir / run_id
        run_state.save(run_dir)
        wf_file = run_dir / "workflow.yml"
        if not wf_file.exists():
            wf_file.write_text(workflow.to_yaml(), encoding="utf-8")
        return run_state

    def _execute_single_step(
        self,
        step: WorkflowStep,
        context: StepContext,
        interactive: bool = True,
        auto_approve: bool = False,
    ) -> StepResult:
        """Execute a single step according to its type."""
        # 1. Slot step (skip if unfilled)
        if step.type == "slot":
            self.console.print(
                f"[dim]↷ 跳过未填充插槽 (Slot): {step.id} ({step.name})[/dim]"
            )
            return StepResult(step_id=step.id, status=StepStatus.SKIPPED)

        # 2. Gate step (Human review checkpoint)
        if step.type == "gate":
            msg = (
                evaluate_expression(step.message, context)
                or f"Review required for step '{step.id}'"
            )
            self.console.print()
            self.console.print(
                Panel(
                    f"[bold yellow]审查节点 (Gate):[/bold yellow] {msg}",
                    border_style="yellow",
                )
            )

            if auto_approve:
                self.console.print("[green]✔ 自动批准 (Auto-approved)[/green]")
                return StepResult(
                    step_id=step.id,
                    status=StepStatus.COMPLETED,
                    output={"choice": "approve"},
                )

            if not interactive:
                # In non-interactive mode without auto-approve, pause workflow
                self.console.print(
                    "[yellow]⏸ 非交互环境：工作流进入暂停 (PAUSED) 状态[/yellow]"
                )
                return StepResult(
                    step_id=step.id,
                    status=StepStatus.PAUSED,
                    output={"message": msg, "options": step.options},
                )

            # Interactive gate selection
            options = step.options or ["approve", "reject"]
            choice = Prompt.ask(
                "请选择操作 (Select option)",
                choices=options,
                default=options[0] if options else "approve",
                console=self.console,
            )

            if choice.lower() == "reject":
                if step.on_reject == "abort":
                    self.console.print("[red]✖ 审查被驳回，工作流终止 (Aborted)[/red]")
                    return StepResult(
                        step_id=step.id,
                        status=StepStatus.ABORTED,
                        output={"choice": choice, "aborted": True},
                    )
                elif step.on_reject == "retry":
                    self.console.print("[yellow]⏸ 审查要求重试，工作流已暂停[/yellow]")
                    return StepResult(
                        step_id=step.id,
                        status=StepStatus.PAUSED,
                        output={"choice": choice},
                    )
                else:  # skip
                    self.console.print(
                        "[dim]↷ 审查驳回但配置为 skip，继续执行后续步骤[/dim]"
                    )
                    return StepResult(
                        step_id=step.id,
                        status=StepStatus.COMPLETED,
                        output={"choice": choice},
                    )

            return StepResult(
                step_id=step.id,
                status=StepStatus.COMPLETED,
                output={"choice": choice},
            )

        # 3. Shell step
        if step.type == "shell":
            raw_cmd = step.run or step.shell
            cmd = evaluate_expression(raw_cmd, context)
            self.console.print(f"[bold cyan]▶ 执行 Shell 命令:[/bold cyan] {cmd}")

            env = dict(os.environ)
            if context.context.get("workflow_dir"):
                env["SPECKIT_WORKFLOW_DIR"] = context.context["workflow_dir"]

            try:
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    text=True,
                    capture_output=True,
                    timeout=step.timeout,
                    cwd=str(self.project_root),
                    env=env,
                )
                output = {
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "exit_code": proc.returncode,
                }
                if proc.stdout.strip():
                    self.console.print(f"[dim]{proc.stdout.strip()}[/dim]")
                if proc.returncode != 0:
                    if proc.stderr.strip():
                        self.console.print(f"[red]{proc.stderr.strip()}[/red]")
                    status = StepStatus.FAILED
                    error = f"Shell command failed with exit code {proc.returncode}"
                else:
                    status = StepStatus.COMPLETED
                    error = None

                return StepResult(
                    step_id=step.id, status=status, output=output, error=error
                )
            except subprocess.TimeoutExpired:
                return StepResult(
                    step_id=step.id,
                    status=StepStatus.FAILED,
                    error=f"Shell command timed out after {step.timeout}s",
                )
            except Exception as e:
                return StepResult(
                    step_id=step.id, status=StepStatus.FAILED, error=str(e)
                )

        # 4. Command step (dispatching Spec Kit command)
        if step.type == "command":
            resolved_input = evaluate_expression(step.input, context)
            resolved_args = evaluate_expression(step.integration_args, context)
            integration = evaluate_expression(step.integration, context) or "auto"

            self.console.print(
                f"[bold cyan]▶ 调度 Spec Kit 指令:[/bold cyan] [green]{step.command}[/green] "
                f"(集成: [yellow]{integration}[/yellow])"
            )
            if resolved_input:
                self.console.print(f"  [dim]参数: {resolved_input}[/dim]")

            # Record successful command dispatch output
            output = {
                "command": step.command,
                "integration": integration,
                "args": resolved_args,
                "input": resolved_input,
                "exit_code": 0,
            }
            return StepResult(
                step_id=step.id, status=StepStatus.COMPLETED, output=output
            )

        # 5. Prompt step
        if step.type == "prompt":
            prompt_text = evaluate_expression(step.prompt, context)
            integration = evaluate_expression(step.integration, context) or "auto"
            self.console.print(
                f"[bold cyan]▶ 发送 Prompt 指令:[/bold cyan] {prompt_text} (集成: {integration})"
            )
            return StepResult(
                step_id=step.id,
                status=StepStatus.COMPLETED,
                output={
                    "prompt": prompt_text,
                    "integration": integration,
                    "exit_code": 0,
                },
            )

        # 6. Init step
        if step.type == "init":
            self.console.print("[bold cyan]▶ 初始化项目结构 (specify init)[/bold cyan]")
            return StepResult(
                step_id=step.id,
                status=StepStatus.COMPLETED,
                output={"initialized": True, "exit_code": 0},
            )

        # Fallback for unrecognized step types
        self.console.print(f"[dim]↷ 执行步骤: {step.id} ({step.type})[/dim]")
        return StepResult(step_id=step.id, status=StepStatus.COMPLETED)

    def execute(
        self,
        run_state: RunState,
        workflow: WorkflowDefinition,
        interactive: bool = True,
        auto_approve: bool = False,
    ) -> RunState:
        """Execute the workflow from its current state."""
        run_state.status = RunStatus.RUNNING
        run_dir = self.runs_dir / run_state.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        context = StepContext(
            inputs=run_state.inputs,
            steps=run_state.step_results,
            context={
                "run_id": run_state.run_id,
                "workflow_dir": run_state.workflow_dir,
            },
            current_step_index=run_state.current_step_index,
        )

        steps = workflow.steps
        total_steps = len(steps)

        while run_state.current_step_index < total_steps:
            step = steps[run_state.current_step_index]
            context.current_step_index = run_state.current_step_index

            self.console.print(
                f"[bold blue]Step [{run_state.current_step_index + 1}/{total_steps}][/bold blue] "
                f"[white]{step.id}[/white] ([dim]{step.type}[/dim])"
            )

            # Handle control flow steps: if, switch, while, do-while
            if step.type == "if":
                cond = evaluate_condition(step.condition, context)
                branch_steps = step.then_steps if cond else step.else_steps
                branch_name = "then" if cond else "else"
                self.console.print(
                    f"[dim]分支判断条件结果: {cond} -> 执行 {branch_name} 分支[/dim]"
                )

                sub_failed = False
                for sub in branch_steps:
                    res = self._execute_single_step(
                        sub, context, interactive, auto_approve
                    )
                    context.steps[sub.id] = res
                    run_state.step_results[sub.id] = res
                    if res.status in (StepStatus.FAILED, StepStatus.ABORTED):
                        sub_failed = True
                        break
                    elif res.status == StepStatus.PAUSED:
                        run_state.status = RunStatus.PAUSED
                        run_state.save(run_dir)
                        return run_state

                step_res = StepResult(
                    step_id=step.id,
                    status=StepStatus.FAILED if sub_failed else StepStatus.COMPLETED,
                    output={"condition": cond, "branch": branch_name},
                )
            elif step.type == "switch":
                expr_val = str(evaluate_expression(step.expression, context))
                matched_steps = step.cases.get(expr_val, step.default_steps)
                self.console.print(
                    f"[dim]Switch 表达式匹配: '{expr_val}' ({len(matched_steps)} 步骤)[/dim]"
                )

                sub_failed = False
                for sub in matched_steps:
                    res = self._execute_single_step(
                        sub, context, interactive, auto_approve
                    )
                    context.steps[sub.id] = res
                    run_state.step_results[sub.id] = res
                    if res.status in (StepStatus.FAILED, StepStatus.ABORTED):
                        sub_failed = True
                        break
                    elif res.status == StepStatus.PAUSED:
                        run_state.status = RunStatus.PAUSED
                        run_state.save(run_dir)
                        return run_state

                step_res = StepResult(
                    step_id=step.id,
                    status=StepStatus.FAILED if sub_failed else StepStatus.COMPLETED,
                    output={"expression": expr_val},
                )
            elif step.type in ("while", "do-while"):
                iteration = 0
                max_iter = step.max_iterations
                is_do_while = step.type == "do-while"

                while iteration < max_iter:
                    if not is_do_while or iteration > 0:
                        cond = evaluate_condition(step.condition, context)
                        if not cond:
                            break

                    iteration += 1
                    self.console.print(
                        f"[dim]循环 [{step.id}] 第 {iteration} 次迭代[/dim]"
                    )
                    iter_failed = False
                    for sub in step.steps:
                        res = self._execute_single_step(
                            sub, context, interactive, auto_approve
                        )
                        context.steps[sub.id] = res
                        run_state.step_results[sub.id] = res
                        if res.status in (StepStatus.FAILED, StepStatus.ABORTED):
                            iter_failed = True
                            break
                        elif res.status == StepStatus.PAUSED:
                            run_state.status = RunStatus.PAUSED
                            run_state.save(run_dir)
                            return run_state
                    if iter_failed:
                        break

                step_res = StepResult(
                    step_id=step.id,
                    status=StepStatus.COMPLETED,
                    output={"iterations": iteration},
                )
            else:
                step_res = self._execute_single_step(
                    step, context, interactive, auto_approve
                )

            # Record step result
            context.steps[step.id] = step_res
            run_state.step_results[step.id] = step_res

            # Status handling
            if step_res.status == StepStatus.PAUSED:
                run_state.status = RunStatus.PAUSED
                run_state.save(run_dir)
                self.console.print(
                    f"[yellow]工作流已暂停在步骤: {step.id} (Run ID: {run_state.run_id})[/yellow]"
                )
                return run_state

            if step_res.status in (StepStatus.FAILED, StepStatus.ABORTED):
                if not step.continue_on_error:
                    run_state.status = (
                        RunStatus.ABORTED
                        if step_res.status == StepStatus.ABORTED
                        else RunStatus.FAILED
                    )
                    run_state.save(run_dir)
                    self.console.print(
                        f"[red]工作流中断于步骤: {step.id} (状态: {run_state.status})[/red]"
                    )
                    return run_state
                else:
                    self.console.print(
                        f"[yellow]步骤 {step.id} 失败，但配置了 continue_on_error，继续执行[/yellow]"
                    )

            # Advance to next step
            run_state.current_step_index += 1
            run_state.save(run_dir)

        run_state.status = RunStatus.COMPLETED
        run_state.save(run_dir)
        self.console.print(
            f"[bold green]✔ 工作流执行完成！(Run ID: {run_state.run_id})[/bold green]"
        )
        return run_state

    def resume(
        self,
        run_id: str,
        choice: str | None = None,
        auto_approve: bool = False,
    ) -> RunState:
        """Resume a paused or failed workflow run."""
        run_dir = self.runs_dir / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Run ID '{run_id}' not found.")

        run_state = RunState.load(run_dir)
        wf_file = run_dir / "workflow.yml"
        if wf_file.exists():
            workflow = WorkflowDefinition.from_yaml(wf_file)
        else:
            workflow = self.load_workflow(run_state.workflow_id)

        # If currently paused at a gate step, and choice is given:
        if run_state.current_step_index < len(workflow.steps):
            current_step = workflow.steps[run_state.current_step_index]
            if current_step.type == "gate" and choice:
                gate_choice = choice.strip()
                if gate_choice == "reject" and current_step.on_reject == "abort":
                    run_state.step_results[current_step.id] = StepResult(
                        step_id=current_step.id,
                        status=StepStatus.ABORTED,
                        output={"choice": gate_choice, "aborted": True},
                    )
                    run_state.status = RunStatus.ABORTED
                    run_state.save(run_dir)
                    return run_state

                run_state.step_results[current_step.id] = StepResult(
                    step_id=current_step.id,
                    status=StepStatus.COMPLETED,
                    output={"choice": gate_choice},
                )
                run_state.current_step_index += 1
                run_state.save(run_dir)

        return self.execute(
            run_state,
            workflow,
            interactive=True,
            auto_approve=auto_approve,
        )

    def get_run(self, run_id: str) -> RunState | None:
        """Get state for a run ID."""
        run_dir = self.runs_dir / run_id
        if not run_dir.exists():
            return None
        try:
            return RunState.load(run_dir)
        except Exception:
            return None

    def list_runs(self) -> list[RunState]:
        """List all runs ordered by creation time descending."""
        if not self.runs_dir.exists():
            return []

        runs: list[RunState] = []
        for d in self.runs_dir.iterdir():
            if d.is_dir() and (d / "state.json").exists():
                try:
                    runs.append(RunState.load(d))
                except Exception:
                    continue

        runs.sort(key=lambda r: r.created_at, reverse=True)
        return runs


__all__ = ["WorkflowEngine"]
