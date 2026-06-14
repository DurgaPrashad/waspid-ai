# Waspid AI OS
"""Workflow runtime: durable run/task store plus the execution engine.

The engine is decoupled from how agents actually run via the
``AgentGateway`` protocol: production wiring (``workflow_live.py``)
launches real Waspid conversations and reads their final messages, while
tests drive the engine with fakes. All state transitions are persisted,
so a restart can resume from the database.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import UUID

from sqlalchemy import Boolean, Integer, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from waspid.app_server.utils.sql_utils import (
    Base,
    UtcDateTime,
    create_json_type_decorator,
    row2dict,
)
from waspid.app_server.workforce.workflow_models import (
    SUPERVISOR_AGENT_NAME,
    WorkflowEventKind,
    WorkflowRun,
    WorkflowRunEvent,
    WorkflowRunStatus,
    WorkflowTask,
    WorkflowTaskStatus,
    build_execution_plan,
)
from waspid.app_server.workforce.workforce_models import (
    AgentSpec,
    WorkforceDefinition,
)

_logger = logging.getLogger(__name__)

DEFAULT_TASK_TIMEOUT = timedelta(minutes=60)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Stored models
# ---------------------------------------------------------------------------


class StoredWorkflowRun(Base):
    __tablename__ = 'workflow_run'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    blueprint_id: Mapped[UUID | None] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    definition: Mapped[WorkforceDefinition] = mapped_column(
        create_json_type_decorator(WorkforceDefinition)
    )
    context: Mapped[dict] = mapped_column(create_json_type_decorator(dict))
    final_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, server_default=func.now(), onupdate=func.now()
    )


class StoredWorkflowTask(Base):
    __tablename__ = 'workflow_task'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    run_id: Mapped[UUID] = mapped_column(index=True)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    conversation_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=2)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_aggregation: Mapped[bool] = mapped_column(Boolean, default=False)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, server_default=func.now(), onupdate=func.now()
    )


class StoredWorkflowRunEvent(Base):
    __tablename__ = 'workflow_run_event'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    run_id: Mapped[UUID] = mapped_column(index=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    agent_name: Mapped[str | None] = mapped_column(String, nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, server_default=func.now(), index=True
    )


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


@dataclass
class WorkflowRunStore:
    """Persistence for runs, tasks, and the run event log."""

    db_session: AsyncSession
    user_id: str | None = None

    async def create_run(self, run: WorkflowRun) -> WorkflowRun:
        stored = StoredWorkflowRun(
            id=run.id,
            user_id=run.user_id,
            blueprint_id=run.blueprint_id,
            name=run.name,
            status=run.status.value,
            definition=run.definition,
            context=run.context,
            final_output=run.final_output,
            error=run.error,
        )
        self.db_session.add(stored)
        await self.db_session.commit()
        await self.db_session.refresh(stored)
        return self._run_from_row(stored)

    async def save_run(self, run: WorkflowRun) -> None:
        stored = await self.db_session.get(StoredWorkflowRun, run.id)
        if stored is None:
            return
        stored.status = run.status.value
        stored.context = run.context
        stored.final_output = run.final_output
        stored.error = run.error
        await self.db_session.commit()

    async def get_run(self, run_id: UUID) -> WorkflowRun | None:
        stmt = select(StoredWorkflowRun).where(
            StoredWorkflowRun.id == run_id,
            StoredWorkflowRun.user_id == self.user_id,
        )
        result = await self.db_session.execute(stmt)
        stored = result.scalar_one_or_none()
        return self._run_from_row(stored) if stored else None

    async def get_run_any_user(self, run_id: UUID) -> WorkflowRun | None:
        """Lookup without user scoping — for webhook-driven callbacks."""
        stored = await self.db_session.get(StoredWorkflowRun, run_id)
        return self._run_from_row(stored) if stored else None

    async def list_runs(self) -> list[WorkflowRun]:
        stmt = (
            select(StoredWorkflowRun)
            .where(StoredWorkflowRun.user_id == self.user_id)
            .order_by(StoredWorkflowRun.created_at.desc())
        )
        result = await self.db_session.execute(stmt)
        return [self._run_from_row(row) for row in result.scalars()]

    async def create_task(self, task: WorkflowTask) -> WorkflowTask:
        stored = StoredWorkflowTask(
            id=task.id,
            run_id=task.run_id,
            agent_name=task.agent_name,
            status=task.status.value,
            conversation_id=task.conversation_id,
            attempts=task.attempts,
            max_attempts=task.max_attempts,
            requires_approval=task.requires_approval,
            approved=task.approved,
            is_aggregation=task.is_aggregation,
            output=task.output,
            error=task.error,
            started_at=task.started_at,
            finished_at=task.finished_at,
        )
        self.db_session.add(stored)
        await self.db_session.commit()
        await self.db_session.refresh(stored)
        return self._task_from_row(stored)

    async def save_task(self, task: WorkflowTask) -> None:
        stored = await self.db_session.get(StoredWorkflowTask, task.id)
        if stored is None:
            return
        stored.status = task.status.value
        stored.conversation_id = task.conversation_id
        stored.attempts = task.attempts
        stored.approved = task.approved
        stored.output = task.output
        stored.error = task.error
        stored.started_at = task.started_at
        stored.finished_at = task.finished_at
        await self.db_session.commit()

    async def get_tasks(self, run_id: UUID) -> list[WorkflowTask]:
        stmt = (
            select(StoredWorkflowTask)
            .where(StoredWorkflowTask.run_id == run_id)
            .order_by(StoredWorkflowTask.created_at)
        )
        result = await self.db_session.execute(stmt)
        return [self._task_from_row(row) for row in result.scalars()]

    async def get_task(self, task_id: UUID) -> WorkflowTask | None:
        stored = await self.db_session.get(StoredWorkflowTask, task_id)
        return self._task_from_row(stored) if stored else None

    async def get_task_by_conversation(
        self, conversation_id: UUID
    ) -> WorkflowTask | None:
        stmt = select(StoredWorkflowTask).where(
            StoredWorkflowTask.conversation_id == conversation_id
        )
        result = await self.db_session.execute(stmt)
        stored = result.scalars().first()
        return self._task_from_row(stored) if stored else None

    async def add_event(
        self,
        run_id: UUID,
        kind: WorkflowEventKind,
        agent_name: str | None = None,
        detail: str | None = None,
    ) -> None:
        event = WorkflowRunEvent(
            run_id=run_id, kind=kind, agent_name=agent_name, detail=detail
        )
        self.db_session.add(
            StoredWorkflowRunEvent(
                id=event.id,
                run_id=event.run_id,
                kind=event.kind.value,
                agent_name=event.agent_name,
                detail=event.detail,
            )
        )
        await self.db_session.commit()

    async def get_events(self, run_id: UUID) -> list[WorkflowRunEvent]:
        stmt = (
            select(StoredWorkflowRunEvent)
            .where(StoredWorkflowRunEvent.run_id == run_id)
            .order_by(StoredWorkflowRunEvent.created_at)
        )
        result = await self.db_session.execute(stmt)
        return [
            WorkflowRunEvent.model_validate(row2dict(row))
            for row in result.scalars()
        ]

    @staticmethod
    def _run_from_row(stored: StoredWorkflowRun) -> WorkflowRun:
        return WorkflowRun.model_validate(row2dict(stored))

    @staticmethod
    def _task_from_row(stored: StoredWorkflowTask) -> WorkflowTask:
        return WorkflowTask.model_validate(row2dict(stored))


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class AgentGateway(Protocol):
    """How the engine launches agents and reads what they produced."""

    async def launch_agent(
        self,
        run: WorkflowRun,
        task: WorkflowTask,
        agent: AgentSpec,
        instructions: str,
        kickoff: str,
    ) -> UUID:
        """Start the agent; returns the conversation id."""
        ...

    async def read_output(self, conversation_id: UUID) -> str | None:
        """Read the agent's final output message."""
        ...


class ActionExecutor(Protocol):
    """Executes integration tool calls attached to workflow edges."""

    async def execute_action(
        self,
        run: WorkflowRun,
        agent_name: str,
        provider: str,
        tool: str,
        params: dict[str, str],
    ) -> tuple[bool, str | None]:
        """Run the tool; returns (ok, error)."""
        ...


def render_action_params(
    params: dict[str, str],
    output: str | None,
    objective: str,
    context: dict[str, str],
) -> dict[str, str]:
    """Substitute {{output}}, {{objective}}, and {{Agent Name}} templates."""
    rendered = {}
    for key, value in params.items():
        value = value.replace('{{output}}', output or '')
        value = value.replace('{{objective}}', objective)
        for agent_name, agent_output in context.items():
            value = value.replace('{{' + agent_name + '}}', agent_output or '')
        rendered[key] = value
    return rendered


@dataclass
class WorkflowRuntime:
    store: WorkflowRunStore
    gateway: AgentGateway
    action_executor: ActionExecutor | None = None
    task_timeout: timedelta = DEFAULT_TASK_TIMEOUT

    # -- lifecycle ---------------------------------------------------------

    async def start_run(
        self,
        definition: WorkforceDefinition,
        name: str | None = None,
        user_id: str | None = None,
        blueprint_id: UUID | None = None,
    ) -> WorkflowRun:
        plan = build_execution_plan(definition)
        run = WorkflowRun(
            user_id=user_id,
            blueprint_id=blueprint_id,
            name=name or definition.objective[:120],
            definition=definition,
        )
        run = await self.store.create_run(run)
        await self.store.add_event(
            run.id,
            WorkflowEventKind.WORKFLOW_STARTED,
            detail=(
                f'{len(definition.agents)} agents; '
                f'dropped cyclic edges: {plan.dropped_edges or "none"}'
            ),
        )
        for agent in definition.agents:
            await self.store.create_task(
                WorkflowTask(
                    run_id=run.id,
                    agent_name=agent.name,
                    requires_approval=agent.name in plan.approval_required,
                )
            )
        await self.dispatch(run.id)
        return run

    async def pause(self, run_id: UUID) -> WorkflowRun | None:
        run = await self.store.get_run(run_id)
        if run is None or run.status != WorkflowRunStatus.RUNNING:
            return run
        run.status = WorkflowRunStatus.PAUSED
        await self.store.save_run(run)
        await self.store.add_event(run.id, WorkflowEventKind.WORKFLOW_PAUSED)
        return run

    async def resume(self, run_id: UUID) -> WorkflowRun | None:
        run = await self.store.get_run(run_id)
        if run is None or run.status != WorkflowRunStatus.PAUSED:
            return run
        run.status = WorkflowRunStatus.RUNNING
        await self.store.save_run(run)
        await self.store.add_event(run.id, WorkflowEventKind.WORKFLOW_RESUMED)
        await self.dispatch(run.id)
        return run

    async def cancel(self, run_id: UUID) -> WorkflowRun | None:
        run = await self.store.get_run(run_id)
        if run is None or run.status in (
            WorkflowRunStatus.COMPLETED,
            WorkflowRunStatus.FAILED,
            WorkflowRunStatus.CANCELLED,
        ):
            return run
        run.status = WorkflowRunStatus.CANCELLED
        await self.store.save_run(run)
        for task in await self.store.get_tasks(run_id):
            if task.status in (
                WorkflowTaskStatus.QUEUED,
                WorkflowTaskStatus.WAITING_APPROVAL,
            ):
                task.status = WorkflowTaskStatus.CANCELLED
                await self.store.save_task(task)
        await self.store.add_event(run.id, WorkflowEventKind.WORKFLOW_CANCELLED)
        return run

    async def approve_task(self, run_id: UUID, task_id: UUID) -> WorkflowTask | None:
        task = await self.store.get_task(task_id)
        if (
            task is None
            or task.run_id != run_id
            or task.status != WorkflowTaskStatus.WAITING_APPROVAL
        ):
            return task
        task.approved = True
        task.status = WorkflowTaskStatus.QUEUED
        await self.store.save_task(task)
        await self.store.add_event(
            run_id, WorkflowEventKind.APPROVAL_GRANTED, agent_name=task.agent_name
        )
        await self.dispatch(run_id)
        return task

    async def retry_task(self, run_id: UUID, task_id: UUID) -> WorkflowTask | None:
        """Manually requeue a failed task (also revives a failed run)."""
        task = await self.store.get_task(task_id)
        if (
            task is None
            or task.run_id != run_id
            or task.status != WorkflowTaskStatus.FAILED
        ):
            return task
        task.status = WorkflowTaskStatus.QUEUED
        task.error = None
        await self.store.save_task(task)
        run = await self.store.get_run_any_user(run_id)
        if run and run.status == WorkflowRunStatus.FAILED:
            run.status = WorkflowRunStatus.RUNNING
            run.error = None
            await self.store.save_run(run)
            await self.store.add_event(run_id, WorkflowEventKind.WORKFLOW_RESUMED)
        await self.dispatch(run_id)
        return task

    # -- engine core -------------------------------------------------------

    async def dispatch(self, run_id: UUID) -> None:
        """Launch every task whose dependencies are satisfied."""
        run = await self.store.get_run_any_user(run_id)
        if run is None or run.status != WorkflowRunStatus.RUNNING:
            return

        plan = build_execution_plan(run.definition)
        tasks = await self.store.get_tasks(run_id)
        completed = {
            t.agent_name
            for t in tasks
            if t.status == WorkflowTaskStatus.COMPLETED and not t.is_aggregation
        }
        graph_tasks = [t for t in tasks if not t.is_aggregation]

        for task in graph_tasks:
            if task.status not in (
                WorkflowTaskStatus.QUEUED,
                WorkflowTaskStatus.WAITING_APPROVAL,
            ):
                continue
            deps = set(plan.deps.get(task.agent_name, []))
            if not deps.issubset(completed):
                continue
            if (
                task.requires_approval
                and not task.approved
                and task.status == WorkflowTaskStatus.QUEUED
            ):
                task.status = WorkflowTaskStatus.WAITING_APPROVAL
                await self.store.save_task(task)
                await self.store.add_event(
                    run_id,
                    WorkflowEventKind.APPROVAL_REQUIRED,
                    agent_name=task.agent_name,
                )
                continue
            if task.status == WorkflowTaskStatus.WAITING_APPROVAL:
                continue
            await self._launch(run, task, deps)

        # All graph tasks done → aggregation, then completion.
        if all(t.status == WorkflowTaskStatus.COMPLETED for t in graph_tasks):
            aggregation = next((t for t in tasks if t.is_aggregation), None)
            if aggregation is None:
                aggregation = await self.store.create_task(
                    WorkflowTask(
                        run_id=run.id,
                        agent_name=self._aggregator(run.definition).name,
                        is_aggregation=True,
                    )
                )
            if aggregation.status == WorkflowTaskStatus.QUEUED:
                await self._launch(run, aggregation, set(completed))

    async def handle_agent_finished(
        self,
        conversation_id: UUID,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Called when an agent's conversation reaches a terminal state."""
        task = await self.store.get_task_by_conversation(conversation_id)
        if task is None or task.status != WorkflowTaskStatus.RUNNING:
            return  # not ours, or already handled (idempotency)
        run = await self.store.get_run_any_user(task.run_id)
        if run is None:
            return

        output = await self.gateway.read_output(conversation_id)
        task.finished_at = _utc_now()

        if success:
            task.status = WorkflowTaskStatus.COMPLETED
            task.output = output
            await self.store.save_task(task)
            await self.store.add_event(
                run.id, WorkflowEventKind.AGENT_COMPLETED, agent_name=task.agent_name
            )
            if task.is_aggregation:
                run.final_output = output
                run.status = WorkflowRunStatus.COMPLETED
                await self.store.save_run(run)
                await self.store.add_event(
                    run.id, WorkflowEventKind.WORKFLOW_COMPLETED
                )
                return
            run.context[task.agent_name] = output or ''
            await self.store.save_run(run)
            await self._fire_edge_actions(run, task.agent_name, output)
            await self.dispatch(run.id)
            return

        await self._record_failure(run, task, error or 'agent run failed')

    async def check_timeouts(self, now: datetime | None = None) -> None:
        """Fail RUNNING tasks that exceeded the timeout (lazy check)."""
        now = now or _utc_now()
        stmt = select(StoredWorkflowTask).where(
            StoredWorkflowTask.status == WorkflowTaskStatus.RUNNING.value
        )
        result = await self.store.db_session.execute(stmt)
        for stored in result.scalars():
            task = self.store._task_from_row(stored)
            if task.started_at is None:
                continue
            started = task.started_at
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            if now - started < self.task_timeout:
                continue
            run = await self.store.get_run_any_user(task.run_id)
            if run is None:
                continue
            task.finished_at = now
            await self.store.add_event(
                run.id, WorkflowEventKind.AGENT_TIMEOUT, agent_name=task.agent_name
            )
            await self._record_failure(run, task, 'agent timed out')

    # -- helpers -----------------------------------------------------------

    async def _fire_edge_actions(
        self, run: WorkflowRun, agent_name: str, output: str | None
    ) -> None:
        """Execute integration actions on edges leaving the finished agent.

        Action failures are logged as run events but do not fail the
        run — actions are side-effects (notifications, CRM updates),
        not workflow steps.
        """
        actions = [
            action
            for edge in run.definition.workflows
            if edge.from_agent == agent_name
            for action in edge.actions
        ]
        if not actions:
            return
        if self.action_executor is None:
            await self.store.add_event(
                run.id,
                WorkflowEventKind.ACTION_FAILED,
                agent_name=agent_name,
                detail='no action executor configured',
            )
            return
        for action in actions:
            params = render_action_params(
                action.params, output, run.definition.objective, run.context
            )
            try:
                ok, error = await self.action_executor.execute_action(
                    run, agent_name, action.provider, action.tool, params
                )
            except Exception as exc:
                ok, error = False, str(exc)
            await self.store.add_event(
                run.id,
                WorkflowEventKind.ACTION_EXECUTED
                if ok
                else WorkflowEventKind.ACTION_FAILED,
                agent_name=agent_name,
                detail=f'{action.provider}.{action.tool}'
                + (f' — {error}' if error else ''),
            )

    async def _launch(
        self, run: WorkflowRun, task: WorkflowTask, deps: set[str]
    ) -> None:
        agent = self._agent_spec(run.definition, task)
        kickoff = self._build_kickoff(run, agent, deps, task.is_aggregation)
        instructions = self._build_instructions(agent)
        task.attempts += 1
        task.started_at = _utc_now()
        try:
            conversation_id = await self.gateway.launch_agent(
                run, task, agent, instructions, kickoff
            )
        except Exception as exc:  # launch itself failed
            _logger.exception('Failed to launch agent %s', task.agent_name)
            await self._record_failure(run, task, f'launch failed: {exc}')
            return
        task.conversation_id = conversation_id
        task.status = WorkflowTaskStatus.RUNNING
        await self.store.save_task(task)
        await self.store.add_event(
            run.id,
            WorkflowEventKind.AGENT_STARTED,
            agent_name=task.agent_name,
            detail=f'attempt {task.attempts}',
        )

    async def _record_failure(
        self, run: WorkflowRun, task: WorkflowTask, error: str
    ) -> None:
        task.error = error
        await self.store.add_event(
            run.id,
            WorkflowEventKind.AGENT_FAILED,
            agent_name=task.agent_name,
            detail=error,
        )
        if task.attempts < task.max_attempts:
            task.status = WorkflowTaskStatus.QUEUED
            task.conversation_id = None
            await self.store.save_task(task)
            await self.store.add_event(
                run.id,
                WorkflowEventKind.AGENT_RETRYING,
                agent_name=task.agent_name,
                detail=f'attempt {task.attempts} of {task.max_attempts} failed',
            )
            await self.dispatch(run.id)
            return
        task.status = WorkflowTaskStatus.FAILED
        await self.store.save_task(task)
        run.status = WorkflowRunStatus.FAILED
        run.error = f'{task.agent_name}: {error}'
        await self.store.save_run(run)
        await self.store.add_event(
            run.id, WorkflowEventKind.WORKFLOW_FAILED, detail=run.error
        )

    def _agent_spec(self, definition: WorkforceDefinition, task: WorkflowTask) -> AgentSpec:
        for agent in definition.agents:
            if agent.name == task.agent_name:
                return agent
        # Synthetic supervisor for aggregation when no coordinator exists.
        return AgentSpec(
            name=SUPERVISOR_AGENT_NAME,
            role='Workforce supervisor',
            system_prompt=(
                'You are the supervisor of an AI workforce. You combine the '
                'outputs of all agents into a single final deliverable.'
            ),
        )

    def _aggregator(self, definition: WorkforceDefinition) -> AgentSpec:
        """The coordinator agent if one exists, else a synthetic supervisor."""
        supervised = {a.reports_to for a in definition.agents if a.reports_to}
        for agent in definition.agents:
            if agent.name in supervised:
                return agent
        return AgentSpec(
            name=SUPERVISOR_AGENT_NAME,
            role='Workforce supervisor',
            system_prompt='You combine agent outputs into a final deliverable.',
        )

    @staticmethod
    def _build_instructions(agent: AgentSpec) -> str:
        parts = [agent.system_prompt, f'Role: {agent.role}']
        if agent.responsibilities:
            parts.append(
                'Responsibilities:\n'
                + '\n'.join(f'- {r}' for r in agent.responsibilities)
            )
        return '\n\n'.join(parts)

    @staticmethod
    def _build_kickoff(
        run: WorkflowRun,
        agent: AgentSpec,
        deps: set[str],
        is_aggregation: bool,
    ) -> str:
        lines = [
            f'You are "{agent.name}" in an AI workforce executing this objective:',
            f'"{run.definition.objective}"',
            '',
        ]
        upstream = (
            sorted(run.context) if is_aggregation else sorted(deps & run.context.keys())
        )
        if upstream:
            lines.append('Outputs from upstream agents (shared workforce memory):')
            for name in upstream:
                output = run.context.get(name) or '(no output captured)'
                lines.append(f'--- {name} ---\n{output}')
            lines.append('')
        if is_aggregation:
            lines.append(
                'Combine all outputs above into the final deliverable for the '
                'objective: a clear, complete report. End with a single final '
                'message containing the full report.'
            )
        else:
            lines.append(
                'Complete your responsibilities now. When you are done, end '
                'with one final message summarizing your results — it will be '
                'passed to the next agent in the workflow.'
            )
        return '\n'.join(lines)
