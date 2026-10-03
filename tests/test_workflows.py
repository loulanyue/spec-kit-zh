"""Comprehensive test suite for Spec Kit Workflows."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry
from specify_cli.workflows.engine import WorkflowEngine
from specify_cli.workflows.expressions import (
    evaluate_condition,
    evaluate_expression,
)
from specify_cli.workflows.models import (
    RunStatus,
    StepStatus,
    WorkflowDefinition,
)

runner = CliRunner()


class TestExpressions:
    """Tests for the expression evaluation engine."""

    def test_basic_interpolation(self):
        ctx = {"inputs": {"name": "Alice", "age": 30}}
        assert evaluate_expression("Hello {{ inputs.name }}!", ctx) == "Hello Alice!"
        assert evaluate_expression("{{ inputs.age }}", ctx) == 30

    def test_nested_steps_and_hyphens(self):
        ctx = {
            "steps": {
                "run-tests": {
                    "status": "COMPLETED",
                    "output": {"exit_code": 0, "file": "report.xml"},
                },
                "build": {
                    "output": {"artifact": "dist/bundle.js"},
                },
            }
        }
        assert evaluate_expression("{{ steps.run-tests.output.exit_code }}", ctx) == 0
        assert evaluate_condition("{{ steps.run-tests.output.exit_code == 0 }}", ctx) is True
        assert evaluate_condition("{{ steps.run-tests.output.exit_code != 0 }}", ctx) is False

    def test_filters(self):
        ctx = {
            "val": "",
            "tags": ["frontend", "react", "ui"],
            "raw_json": '{"status": "ok", "items": [1, 2, 3]}',
            "users": [{"name": "Bob"}, {"name": "Charlie"}],
        }
        # default
        assert evaluate_expression("{{ val | default('fallback') }}", ctx) == "fallback"
        # join
        assert evaluate_expression("{{ tags | join(';') }}", ctx) == "frontend;react;ui"
        # contains
        assert evaluate_expression("{{ tags | contains('react') }}", ctx) is True
        assert evaluate_expression("{{ tags | contains('vue') }}", ctx) is False
        # map
        assert evaluate_expression("{{ users | map('name') }}", ctx) == ["Bob", "Charlie"]
        # from_json
        res = evaluate_expression("{{ raw_json | from_json }}", ctx)
        assert res["status"] == "ok"
        assert res["items"] == [1, 2, 3]

    def test_boolean_logic_and_comparisons(self):
        ctx = {"count": 10, "ready": True, "target": "prod"}
        assert evaluate_condition("{{ count > 5 and ready }}", ctx) is True
        assert evaluate_condition("{{ count < 5 or target == 'dev' }}", ctx) is False
        assert evaluate_condition("{{ target in ['prod', 'stage'] }}", ctx) is True


class TestWorkflowModelsAndParsing:
    """Tests for workflow models and YAML loading."""

    def test_load_bundled_speckit(self):
        engine = WorkflowEngine()
        wf = engine.load_workflow("speckit")
        assert wf.id == "speckit"
        assert len(wf.steps) == 6
        assert "spec" in wf.inputs
        assert wf.inputs["spec"].required is True
        assert wf.inputs["integration"].default == "auto"

    def test_load_bundled_bugfix(self):
        engine = WorkflowEngine()
        wf = engine.load_workflow("bugfix")
        assert wf.id == "bugfix"
        assert len(wf.steps) == 4
        assert "report" in wf.inputs
        assert "slug" in wf.inputs

    def test_input_coercion(self):
        yaml_content = """
schema_version: "1.0"
workflow:
  id: "test-inputs"
  name: "Test Inputs"
inputs:
  num:
    type: number
    default: 10
  flag:
    type: boolean
    default: false
  mode:
    type: string
    enum: ["fast", "slow"]
    default: "fast"
steps:
  - id: step1
    type: shell
    run: echo ok
"""
        wf = WorkflowDefinition.from_yaml(yaml_content)
        engine = WorkflowEngine()

        # Coerce valid inputs
        res = engine._resolve_inputs(wf, {"num": "42", "flag": "true", "mode": "slow"})
        assert res["num"] == 42
        assert res["flag"] is True
        assert res["mode"] == "slow"

        # Missing required
        from specify_cli.workflows.models import WorkflowInput
        wf.inputs["req"] = WorkflowInput(name="req", type="string", required=True)
        with pytest.raises(ValueError, match="Missing required workflow input"):
            engine._resolve_inputs(wf, {})

        # Invalid enum
        with pytest.raises(ValueError, match="must be one of"):
            engine._resolve_inputs(wf, {"req": "value", "mode": "invalid"})


class TestWorkflowExecution:
    """Tests for WorkflowEngine execution and resume."""

    def test_shell_step_execution(self, tmp_path):
        yaml_content = """
schema_version: "1.0"
workflow:
  id: "shell-test"
  name: "Shell Test"
steps:
  - id: write-file
    type: shell
    run: "echo 'hello workflow' > test.txt"
  - id: read-file
    type: shell
    run: "cat test.txt"
"""
        wf = WorkflowDefinition.from_yaml(yaml_content)
        engine = WorkflowEngine(project_root=tmp_path)
        run = engine.create_run(wf, {})
        res = engine.execute(run, wf, interactive=False)

        assert res.status == RunStatus.COMPLETED
        assert (tmp_path / "test.txt").read_text().strip() == "hello workflow"
        assert res.step_results["read-file"].output["stdout"].strip() == "hello workflow"

    def test_gate_step_pause_and_resume(self, tmp_path):
        yaml_content = """
schema_version: "1.0"
workflow:
  id: "gate-test"
  name: "Gate Test"
steps:
  - id: step-one
    type: shell
    run: "echo step 1"
  - id: review
    type: gate
    message: "Do you want to proceed?"
    options: [approve, reject]
    on_reject: abort
  - id: step-two
    type: shell
    run: "echo step 2"
"""
        wf = WorkflowDefinition.from_yaml(yaml_content)
        engine = WorkflowEngine(project_root=tmp_path)
        run = engine.create_run(wf, {})

        # Non-interactive without auto-approve should pause at gate
        paused_state = engine.execute(run, wf, interactive=False, auto_approve=False)
        assert paused_state.status == RunStatus.PAUSED
        assert paused_state.current_step_index == 1
        assert "step-one" in paused_state.step_results

        # Resume with choice='approve'
        resumed_state = engine.resume(paused_state.run_id, choice="approve", auto_approve=True)
        assert resumed_state.status == RunStatus.COMPLETED
        assert resumed_state.step_results["review"].status == StepStatus.COMPLETED
        assert resumed_state.step_results["step-two"].status == StepStatus.COMPLETED

    def test_gate_step_abort(self, tmp_path):
        yaml_content = """
schema_version: "1.0"
workflow:
  id: "gate-abort-test"
  name: "Gate Abort Test"
steps:
  - id: review
    type: gate
    options: [approve, reject]
    on_reject: abort
  - id: never-reached
    type: shell
    run: "echo never"
"""
        wf = WorkflowDefinition.from_yaml(yaml_content)
        engine = WorkflowEngine(project_root=tmp_path)
        run = engine.create_run(wf, {})

        # Pause
        engine.execute(run, wf, interactive=False, auto_approve=False)
        # Resume with reject
        aborted = engine.resume(run.run_id, choice="reject")
        assert aborted.status == RunStatus.ABORTED
        assert "never-reached" not in aborted.step_results

    def test_if_branching(self, tmp_path):
        yaml_content = """
schema_version: "1.0"
workflow:
  id: "if-test"
  name: "If Test"
inputs:
  branch:
    type: string
    default: "a"
steps:
  - id: check-branch
    type: if
    condition: "{{ inputs.branch == 'a' }}"
    then:
      - id: branch-a
        type: shell
        run: "echo ran A"
    else:
      - id: branch-b
        type: shell
        run: "echo ran B"
"""
        wf = WorkflowDefinition.from_yaml(yaml_content)
        engine = WorkflowEngine(project_root=tmp_path)

        # Run branch A
        run_a = engine.create_run(wf, {"branch": "a"})
        res_a = engine.execute(run_a, wf, interactive=False)
        assert res_a.status == RunStatus.COMPLETED
        assert "branch-a" in res_a.step_results
        assert "branch-b" not in res_a.step_results

        # Run branch B
        run_b = engine.create_run(wf, {"branch": "b"})
        res_b = engine.execute(run_b, wf, interactive=False)
        assert res_b.status == RunStatus.COMPLETED
        assert "branch-b" in res_b.step_results
        assert "branch-a" not in res_b.step_results


class TestWorkflowCatalogAndRegistry:
    """Tests for catalog discovery and local registry."""

    def test_catalog_discovery(self):
        catalog = WorkflowCatalog()
        wfs = catalog.get_all_workflows()
        ids = [w.id for w in wfs]
        assert "speckit" in ids
        assert "bugfix" in ids
        assert "assess" in ids

    def test_catalog_search(self):
        catalog = WorkflowCatalog()
        res = catalog.search("bug")
        assert any(w.id == "bugfix" for w in res)

    def test_registry_install_and_uninstall(self, tmp_path):
        reg = WorkflowRegistry(project_root=tmp_path)
        wf = reg.install("speckit")
        assert wf.id == "speckit"
        assert (tmp_path / ".specify" / "workflows" / "speckit" / "workflow.yml").exists()

        installed = reg.list_installed()
        assert len(installed) == 1
        assert installed[0].id == "speckit"

        # Uninstall
        assert reg.uninstall("speckit") is True
        assert len(reg.list_installed()) == 0


class TestWorkflowCLI:
    """Tests for Typer CLI commands."""

    def test_cli_workflow_help(self):
        result = runner.invoke(app, ["workflow", "--help"])
        assert result.exit_code == 0
        assert "run" in result.output
        assert "list" in result.output
        assert "info" in result.output
        assert "catalog" in result.output

    def test_cli_workflow_info(self):
        result = runner.invoke(app, ["workflow", "info", "speckit"])
        assert result.exit_code == 0
        assert "Full SDD Cycle" in result.output
        assert "spec" in result.output

    def test_cli_workflow_list_available(self):
        result = runner.invoke(app, ["workflow", "list", "--available"])
        assert result.exit_code == 0
        assert "speckit" in result.output

    def test_cli_workflow_run_speckit(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["workflow", "run", "speckit", "--input", "spec=Test App", "--auto-approve"],
        )
        assert result.exit_code == 0
        assert "工作流执行完成" in result.output
