# Waspid AI OS
"""Models and execution planning for the workflow runtime."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from waspid.app_server.workforce.workforce_models import WorkforceDefinition

# Synthetic agent name used for the final aggregation step when the
# definition has no coordinator of its own.
SUPERVISOR_AGENT_NAME = 'Supervisor'


class WorkflowRunStatus(str, Enum):
    RUNNING = 'RUNNING'
    PAUSED = 'PAUSED'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'


class WorkflowTaskStatus(str, Enum):
    QUEUED = 'QUEUED'
    WAITING_APPROVAL = 'WAITING_APPROVAL'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'


class WorkflowEventKind(str, Enum):
    WORKFLOW_STARTED = 'workflow_started'
    WORKFLOW_PAUSED = 'workflow_paused'
    WORKFLOW_RESUMED = 'workflow_resumed'
    WORKFLOW_COMPLETED = 'workflow_completed'
    WORKFLOW_FAILED = 'workflow_failed'
    WORKFLOW_CANCELLED = 'workflow_cancelled'
    AGENT_STARTED = 'agent_started'
    AGENT_COMPLETED = 'agent_completed'
    AGENT_FAILED = 'agent_failed'
    AGENT_RETRYING = 'agent_retrying'
    AGENT_TIMEOUT = 'agent_timeout'
    APPROVAL_REQUIRED = 'approval_required'
    APPROVAL_GRANTED = 'approval_granted'
    ACTION_EXECUTED = 'action_executed'
    ACTION_FAILED = 'action_failed'


class WorkflowTask(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    agent_name: str
    status: WorkflowTaskStatus = WorkflowTaskStatus.QUEUED
    conversation_id: UUID | None = None
    attempts: int = 0
    max_attempts: int = 2
    requires_approval: bool = False
    approved: bool = False
    is_aggregation: bool = False
    output: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkflowRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str | None = None
    blueprint_id: UUID | None = None
    name: str
    status: WorkflowRunStatus = WorkflowRunStatus.RUNNING
    definition: WorkforceDefinition
    # Shared workforce memory: agent name -> final output, passed to
    # downstream agents at launch.
    context: dict[str, str] = Field(default_factory=dict)
    final_output: str | None = None
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkflowRunEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    kind: WorkflowEventKind
    agent_name: str | None = None
    detail: str | None = None
    created_at: datetime | None = None


class WorkflowRunDetail(BaseModel):
    """Run plus its tasks and event log, as returned by the API."""

    run: WorkflowRun
    tasks: list[WorkflowTask]
    events: list[WorkflowRunEvent]


class StartWorkflowRunRequest(BaseModel):
    blueprint_id: UUID | None = None
    definition: WorkforceDefinition | None = None
    name: str | None = None
    # Deploy even if requirement checks (LLM, integrations) fail.
    ignore_missing_requirements: bool = False


class WorkflowRunPage(BaseModel):
    items: list[WorkflowRun]


class ExecutionPlan(BaseModel):
    """Dependency structure derived from a workforce definition.

    ``deps`` maps each agent to the set of upstream agents that must
    complete before it may start. Cycles in the generated edge list are
    broken deterministically (depth-first in agent order; back-edges are
    dropped and reported in ``dropped_edges``).
    """

    deps: dict[str, list[str]]
    approval_required: list[str]
    dropped_edges: list[str]


def build_execution_plan(definition: WorkforceDefinition) -> ExecutionPlan:
    agent_names = [a.name for a in definition.agents]
    name_set = set(agent_names)

    # Dedupe edges, drop self-loops and edges to unknown agents.
    edges: list[tuple[str, str, bool]] = []
    seen_edges: set[tuple[str, str]] = set()
    for edge in definition.workflows:
        key = (edge.from_agent, edge.to_agent)
        if (
            edge.from_agent not in name_set
            or edge.to_agent not in name_set
            or edge.from_agent == edge.to_agent
            or key in seen_edges
        ):
            continue
        seen_edges.add(key)
        edges.append((edge.from_agent, edge.to_agent, edge.requires_approval))

    # Break cycles: DFS in deterministic order; an edge that points back
    # into the current stack is a back-edge and gets dropped.
    outgoing: dict[str, list[str]] = {name: [] for name in agent_names}
    for from_agent, to_agent, _ in edges:
        outgoing[from_agent].append(to_agent)

    dropped: set[tuple[str, str]] = set()
    visited: set[str] = set()
    stack: set[str] = set()

    def visit(node: str) -> None:
        visited.add(node)
        stack.add(node)
        for neighbor in outgoing[node]:
            if neighbor in stack:
                dropped.add((node, neighbor))
            elif neighbor not in visited:
                visit(neighbor)
        stack.discard(node)

    for name in agent_names:
        if name not in visited:
            visit(name)

    deps: dict[str, list[str]] = {name: [] for name in agent_names}
    approval: set[str] = set()
    for from_agent, to_agent, requires_approval in edges:
        if (from_agent, to_agent) in dropped:
            continue
        deps[to_agent].append(from_agent)
        if requires_approval:
            approval.add(to_agent)

    return ExecutionPlan(
        deps=deps,
        approval_required=sorted(approval),
        dropped_edges=[f'{a}->{b}' for a, b in sorted(dropped)],
    )
