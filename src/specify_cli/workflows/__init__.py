"""Spec Kit Workflows module.

Provides multi-step automation pipelines for Spec-Driven Development,
interactive human review gates, expression evaluation, catalog discovery,
and state machine execution.
"""

from __future__ import annotations

from specify_cli.workflows.catalog import (
    WorkflowCatalog,
    WorkflowCatalogEntry,
    WorkflowRegistry,
)
from specify_cli.workflows.cli import catalog_app, workflow_app
from specify_cli.workflows.engine import WorkflowEngine
from specify_cli.workflows.expressions import (
    evaluate_condition,
    evaluate_expression,
)
from specify_cli.workflows.models import (
    RunState,
    RunStatus,
    StepContext,
    StepResult,
    StepStatus,
    WorkflowDefinition,
    WorkflowInput,
    WorkflowStep,
)

__all__ = [
    "RunState",
    "RunStatus",
    "StepContext",
    "StepResult",
    "StepStatus",
    "WorkflowCatalog",
    "WorkflowCatalogEntry",
    "WorkflowDefinition",
    "WorkflowEngine",
    "WorkflowInput",
    "WorkflowRegistry",
    "WorkflowStep",
    "catalog_app",
    "evaluate_condition",
    "evaluate_expression",
    "workflow_app",
]
