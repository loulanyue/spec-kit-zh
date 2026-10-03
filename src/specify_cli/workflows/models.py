"""Data models and state representations for Spec Kit Workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class StepStatus(str, Enum):
    """Execution status for a single workflow step."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    SKIPPED = "SKIPPED"


class RunStatus(str, Enum):
    """Overall execution status for a workflow run."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


@dataclass
class WorkflowInput:
    """Specification of an input argument for a workflow."""

    name: str
    type: str = "string"  # string, number, boolean, enum
    required: bool = False
    default: Any = None
    prompt: str = ""
    enum: list[Any] | None = None

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> WorkflowInput:
        return cls(
            name=name,
            type=str(data.get("type", "string")).lower(),
            required=bool(data.get("required", False)),
            default=data.get("default"),
            prompt=str(data.get("prompt", "")),
            enum=data.get("enum"),
        )


@dataclass
class WorkflowStep:
    """Single step within a workflow definition."""

    id: str
    type: str = "command"  # command, gate, shell, init, prompt, if, switch, while, do-while, slot, fan-out, fan-in
    command: str = ""
    run: str = ""
    shell: str = ""
    prompt: str = ""
    message: str = ""
    options: list[str] = field(default_factory=lambda: ["approve", "reject"])
    on_reject: str = "abort"  # abort, skip, retry
    input: dict[str, Any] = field(default_factory=dict)
    integration: str = "auto"
    integration_args: list[str] = field(default_factory=list)
    integration_options: dict[str, Any] = field(default_factory=dict)
    model: str = ""
    timeout: int = 300
    continue_on_error: bool = False
    condition: str = ""
    expression: str = ""
    then_steps: list[WorkflowStep] = field(default_factory=list)
    else_steps: list[WorkflowStep] = field(default_factory=list)
    cases: dict[str, list[WorkflowStep]] = field(default_factory=dict)
    default_steps: list[WorkflowStep] = field(default_factory=list)
    max_iterations: int = 10
    steps: list[WorkflowStep] = field(default_factory=list)
    items: Any = None
    max_concurrency: int = 1
    sub_step: WorkflowStep | None = None
    wait_for: list[str] = field(default_factory=list)
    name: str = ""
    raw_step: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowStep:
        step_id = str(data.get("id", ""))
        step_type = str(data.get("type", "command")).lower()
        if "command" in data and "type" not in data:
            step_type = "command"
        elif "shell" in data or "run" in data:
            if "type" not in data:
                step_type = "shell"

        run_cmd = str(data.get("run", "") or data.get("shell", ""))
        timeout = int(data.get("timeout", 300))
        continue_on_error = bool(data.get("continue_on_error", False))
        options = data.get("options")
        if options is None:
            options = ["approve", "reject"]
        elif not isinstance(options, list):
            options = [str(options)]
        else:
            options = [str(opt) for opt in options]

        then_raw = data.get("then", [])
        then_steps = (
            [cls.from_dict(s) for s in then_raw] if isinstance(then_raw, list) else []
        )

        else_raw = data.get("else", [])
        else_steps = (
            [cls.from_dict(s) for s in else_raw] if isinstance(else_raw, list) else []
        )

        cases_raw = data.get("cases", {})
        cases: dict[str, list[WorkflowStep]] = {}
        if isinstance(cases_raw, dict):
            for k, steps_list in cases_raw.items():
                if isinstance(steps_list, list):
                    cases[k] = [cls.from_dict(s) for s in steps_list]

        default_raw = data.get("default", [])
        default_steps = (
            [cls.from_dict(s) for s in default_raw]
            if isinstance(default_raw, list)
            else []
        )

        sub_steps_raw = data.get("steps", [])
        sub_steps = (
            [cls.from_dict(s) for s in sub_steps_raw]
            if isinstance(sub_steps_raw, list)
            else []
        )

        sub_step_raw = data.get("step")
        sub_step = (
            cls.from_dict(sub_step_raw) if isinstance(sub_step_raw, dict) else None
        )

        return cls(
            id=step_id,
            type=step_type,
            command=str(data.get("command", "")),
            run=run_cmd,
            shell=run_cmd,
            prompt=str(data.get("prompt", "")),
            message=str(data.get("message", "")),
            options=options,
            on_reject=str(data.get("on_reject", "abort")).lower(),
            input=data.get("input", {}) if isinstance(data.get("input"), dict) else {},
            integration=str(data.get("integration", "auto")),
            integration_args=list(data.get("integration_args", []))
            if isinstance(data.get("integration_args"), list)
            else [],
            integration_options=data.get("integration_options", {})
            if isinstance(data.get("integration_options"), dict)
            else {},
            model=str(data.get("model", "")),
            timeout=timeout,
            continue_on_error=continue_on_error,
            condition=str(data.get("condition", "")),
            expression=str(data.get("expression", "")),
            then_steps=then_steps,
            else_steps=else_steps,
            cases=cases,
            default_steps=default_steps,
            max_iterations=int(data.get("max_iterations", 10)),
            steps=sub_steps,
            items=data.get("items"),
            max_concurrency=int(data.get("max_concurrency", 1)),
            sub_step=sub_step,
            wait_for=list(data.get("wait_for", []))
            if isinstance(data.get("wait_for"), list)
            else [],
            name=str(data.get("name", "")),
            raw_step=data,
        )


@dataclass
class WorkflowDefinition:
    """Loaded workflow definition."""

    id: str
    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    requires: dict[str, Any] = field(default_factory=dict)
    inputs: dict[str, WorkflowInput] = field(default_factory=dict)
    steps: list[WorkflowStep] = field(default_factory=list)
    path: Path | None = None
    schema_version: str = "1.0"
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_yaml(self) -> str:
        if self.raw_data:
            return yaml.safe_dump(self.raw_data, sort_keys=False)
        data = {
            "schema_version": self.schema_version,
            "workflow": {
                "id": self.id,
                "name": self.name,
                "version": self.version,
                "author": self.author,
                "description": self.description,
            },
            "requires": self.requires,
            "inputs": {
                k: {
                    "type": v.type,
                    "required": v.required,
                    "default": v.default,
                    "prompt": v.prompt,
                }
                for k, v in self.inputs.items()
            },
            "steps": [s.raw_step for s in self.steps],
        }
        return yaml.safe_dump(data, sort_keys=False)

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], path: Path | None = None
    ) -> WorkflowDefinition:
        wf_meta = data.get("workflow", {})
        wf_id = str(wf_meta.get("id", data.get("id", "")))
        wf_name = str(wf_meta.get("name", data.get("name", wf_id)))
        wf_version = str(wf_meta.get("version", data.get("version", "1.0.0")))
        wf_author = str(wf_meta.get("author", data.get("author", "")))
        wf_desc = str(wf_meta.get("description", data.get("description", "")))
        schema_version = str(data.get("schema_version", "1.0"))

        inputs_data = data.get("inputs", {})
        inputs: dict[str, WorkflowInput] = {}
        if isinstance(inputs_data, dict):
            for in_name, in_def in inputs_data.items():
                if isinstance(in_def, dict):
                    inputs[in_name] = WorkflowInput.from_dict(in_name, in_def)

        steps_data = data.get("steps", [])
        steps: list[WorkflowStep] = []
        if isinstance(steps_data, list):
            for s_data in steps_data:
                if isinstance(s_data, dict):
                    steps.append(WorkflowStep.from_dict(s_data))

        return cls(
            id=wf_id,
            name=wf_name,
            version=wf_version,
            author=wf_author,
            description=wf_desc,
            requires=data.get("requires", {})
            if isinstance(data.get("requires"), dict)
            else {},
            inputs=inputs,
            steps=steps,
            path=path,
            schema_version=schema_version,
            raw_data=data,
        )

    @classmethod
    def from_yaml(cls, path_or_str: str | Path) -> WorkflowDefinition:
        if isinstance(path_or_str, Path) or (
            isinstance(path_or_str, str)
            and ("\n" not in path_or_str and Path(path_or_str).exists())
        ):
            path = Path(path_or_str)
            text = path.read_text(encoding="utf-8")
            data = yaml.safe_load(text) or {}
            return cls.from_dict(data, path=path)
        data = yaml.safe_load(str(path_or_str)) or {}
        return cls.from_dict(data)


@dataclass
class StepResult:
    """Execution result for a single step."""

    step_id: str
    status: str  # COMPLETED, FAILED, SKIPPED, ABORTED, PAUSED
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "status": self.status,
            "output": self.output,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StepResult:
        return cls(
            step_id=str(data.get("step_id", "")),
            status=str(data.get("status", StepStatus.COMPLETED)),
            output=data.get("output", {})
            if isinstance(data.get("output"), dict)
            else {},
            error=data.get("error"),
        )


@dataclass
class StepContext:
    """Runtime context passed to step executions and expression evaluations."""

    inputs: dict[str, Any] = field(default_factory=dict)
    steps: dict[str, StepResult] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    current_step_index: int = 0

    def to_namespace(self) -> dict[str, Any]:
        """Convert to evaluation namespace for expressions."""
        step_outputs = {}
        for sid, res in self.steps.items():
            step_outputs[sid] = {
                "status": res.status,
                "output": res.output,
                "error": res.error,
            }
        return {
            "inputs": self.inputs,
            "steps": step_outputs,
            "context": self.context,
        }


@dataclass
class RunState:
    """Overall execution state for a workflow run."""

    run_id: str
    workflow_id: str
    status: str = RunStatus.RUNNING  # RUNNING, COMPLETED, PAUSED, FAILED, ABORTED
    inputs: dict[str, Any] = field(default_factory=dict)
    step_results: dict[str, StepResult] = field(default_factory=dict)
    current_step_index: int = 0
    workflow_dir: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "inputs": self.inputs,
            "step_results": {k: v.to_dict() for k, v in self.step_results.items()},
            "current_step_index": self.current_step_index,
            "workflow_dir": self.workflow_dir,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunState:
        raw_results = data.get("step_results", {})
        results: dict[str, StepResult] = {}
        if isinstance(raw_results, dict):
            for k, v in raw_results.items():
                if isinstance(v, dict):
                    results[k] = StepResult.from_dict(v)

        return cls(
            run_id=str(data.get("run_id", "")),
            workflow_id=str(data.get("workflow_id", "")),
            status=str(data.get("status", RunStatus.RUNNING)),
            inputs=data.get("inputs", {})
            if isinstance(data.get("inputs"), dict)
            else {},
            step_results=results,
            current_step_index=int(data.get("current_step_index", 0)),
            workflow_dir=str(data.get("workflow_dir", "")),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
        )

    def save(self, run_dir: Path) -> Path:
        """Persist state to run_dir/state.json and inputs to run_dir/inputs.json."""
        run_dir.mkdir(parents=True, exist_ok=True)
        self.updated_at = datetime.now(timezone.utc).isoformat()
        state_file = run_dir / "state.json"
        state_file.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        inputs_file = run_dir / "inputs.json"
        inputs_file.write_text(
            json.dumps(self.inputs, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return state_file

    @classmethod
    def load(cls, run_dir: Path) -> RunState:
        state_file = run_dir / "state.json"
        if not state_file.exists():
            raise FileNotFoundError(f"Run state not found: {state_file}")
        data = json.loads(state_file.read_text(encoding="utf-8"))
        return cls.from_dict(data)


__all__ = [
    "RunState",
    "RunStatus",
    "StepContext",
    "StepResult",
    "StepStatus",
    "WorkflowDefinition",
    "WorkflowInput",
    "WorkflowStep",
]
