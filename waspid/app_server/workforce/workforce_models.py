# Waspid AI OS
"""Pydantic models for the workforce agent factory."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# Version stamp for exported blueprints so future schema changes can be
# migrated on import.
BLUEPRINT_EXPORT_VERSION = 1

# Tool identifiers the architect may assign to generated agents. These map
# onto capabilities available in a Waspid sandbox today; anything else an
# LLM invents is dropped during normalization rather than presented as a
# capability that does not exist.
KNOWN_AGENT_TOOLS = (
    'terminal',
    'code_editor',
    'browser',
    'web_search',
    'git',
    'file_storage',
    'mcp',
)


class AgentSpec(BaseModel):
    """A single generated agent: role, prompt, and wiring."""

    name: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=200)
    responsibilities: list[str] = Field(default_factory=list, max_length=20)
    system_prompt: str = Field(min_length=1, max_length=20000)
    tools: list[str] = Field(default_factory=list, max_length=20)
    integrations: list[str] = Field(default_factory=list, max_length=20)
    # Name of the supervising agent in the same workforce, if any.
    reports_to: str | None = None


class WorkflowAction(BaseModel):
    """An integration tool call fired when a handoff edge triggers.

    ``params`` values support templating: ``{{output}}`` (the upstream
    agent's final output), ``{{objective}}``, and ``{{<Agent Name>}}``
    (any completed agent's output from shared memory).
    """

    provider: str
    tool: str
    params: dict[str, str] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    """A directed handoff between two agents in the workforce."""

    from_agent: str
    to_agent: str
    # Human-readable handoff condition, e.g. "lead qualified".
    trigger: str = ''
    # When True, the downstream agent does not start until a human
    # approves the handoff (the run pauses at this point).
    requires_approval: bool = False
    # Integration tool calls executed when this edge fires.
    actions: list[WorkflowAction] = Field(default_factory=list)


class WorkforceDefinition(BaseModel):
    """A complete generated workforce: the agent factory's output.

    Size caps bound storage and execution cost — imports and API
    payloads are rejected beyond them, not silently truncated.
    """

    objective: str = Field(min_length=1, max_length=4000)
    summary: str = Field(default='', max_length=4000)
    agents: list[AgentSpec] = Field(default_factory=list, max_length=100)
    workflows: list[WorkflowEdge] = Field(default_factory=list, max_length=500)


class WorkforceBlueprint(BaseModel):
    """A persisted, reusable workforce definition."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str | None = None
    name: str = Field(min_length=1, max_length=200)
    definition: WorkforceDefinition
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GenerateWorkforceRequest(BaseModel):
    objective: str = Field(min_length=1, max_length=4000)
    max_agents: int = Field(default=12, ge=1, le=100)


class CreateBlueprintRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    definition: WorkforceDefinition


class BlueprintExport(BaseModel):
    """Portable blueprint format for export/import and sharing."""

    version: int = BLUEPRINT_EXPORT_VERSION
    name: str
    definition: WorkforceDefinition


class WorkforceBlueprintPage(BaseModel):
    items: list[WorkforceBlueprint]


class WorkforceRequirements(BaseModel):
    """What a workforce definition needs before it can deploy.

    Derived from the definition itself: integration providers referenced
    by workflow edge actions and by agents' ``integrations`` lists, plus
    a configured LLM (every agent run needs one).
    """

    llm_configured: bool
    required_integrations: list[str]
    missing_integrations: list[str]

    @property
    def satisfied(self) -> bool:
        return self.llm_configured and not self.missing_integrations


def required_integration_providers(
    definition: WorkforceDefinition, known_providers: set[str]
) -> list[str]:
    """Providers this workforce depends on, restricted to real registry ids."""
    required: set[str] = set()
    for edge in definition.workflows:
        for action in edge.actions:
            required.add(action.provider)
    for agent in definition.agents:
        for integration in agent.integrations:
            normalized = integration.strip().lower()
            if normalized in known_providers:
                required.add(normalized)
    return sorted(required & known_providers)
