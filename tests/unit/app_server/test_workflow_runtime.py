# Waspid AI OS
"""Tests for the workflow runtime engine (agent execution faked).

The fake gateway records every launch and lets tests fire completions,
exercising the full autonomous loop: dispatch → launch → finish →
handoff → aggregation → final output.
"""

from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from waspid.app_server.utils.sql_utils import Base
from waspid.app_server.workforce.workflow_models import (
    SUPERVISOR_AGENT_NAME,
    WorkflowEventKind,
    WorkflowRunStatus,
    WorkflowTaskStatus,
    build_execution_plan,
)
from waspid.app_server.workforce.workflow_run_service import (
    WorkflowRunStore,
    WorkflowRuntime,
)
from waspid.app_server.workforce.workforce_models import (
    AgentSpec,
    WorkflowEdge,
    WorkforceDefinition,
)


class FakeGateway:
    """Records launches; outputs are configured per agent name."""

    def __init__(self):
        self.launches = []  # (agent_name, kickoff, conversation_id)
        self.outputs: dict[UUID, str] = {}
        self.fail_launch_for: set[str] = set()

    async def launch_agent(self, run, task, agent, instructions, kickoff):
        if agent.name in self.fail_launch_for:
            raise RuntimeError('boom')
        conversation_id = uuid4()
        self.launches.append((agent.name, kickoff, conversation_id))
        self.outputs[conversation_id] = f'output of {agent.name}'
        return conversation_id

    async def read_output(self, conversation_id):
        return self.outputs.get(conversation_id)

    def conversation_for(self, agent_name, occurrence=0):
        matches = [c for (n, _, c) in self.launches if n == agent_name]
        return matches[occurrence]

    def launched_names(self):
        return [n for (n, _, _) in self.launches]


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db_session:
        yield db_session
    await engine.dispose()


@pytest.fixture
def gateway() -> FakeGateway:
    return FakeGateway()


@pytest.fixture
def runtime(async_session, gateway) -> WorkflowRuntime:
    return WorkflowRuntime(
        store=WorkflowRunStore(db_session=async_session), gateway=gateway
    )


def agent(name, reports_to=None):
    return AgentSpec(
        name=name, role=f'{name} role', system_prompt=f'You are {name}.',
        reports_to=reports_to,
    )


def chain_definition() -> WorkforceDefinition:
    """Manager (coordinator) + Research -> Qualify -> CRM chain."""
    return WorkforceDefinition(
        objective='Run a real estate lead generation business',
        agents=[
            agent('Manager'),
            agent('Research', reports_to='Manager'),
            agent('Qualify', reports_to='Manager'),
            agent('CRM', reports_to='Manager'),
        ],
        workflows=[
            WorkflowEdge(from_agent='Research', to_agent='Qualify'),
            WorkflowEdge(from_agent='Qualify', to_agent='CRM'),
            WorkflowEdge(from_agent='CRM', to_agent='Manager'),
        ],
    )


async def finish(runtime, gateway, agent_name, occurrence=0, success=True):
    await runtime.handle_agent_finished(
        gateway.conversation_for(agent_name, occurrence), success=success,
        error=None if success else 'it broke',
    )


# ---------------------------------------------------------------------------
# Plan building
# ---------------------------------------------------------------------------


def test_plan_linear_chain():
    plan = build_execution_plan(chain_definition())
    assert plan.deps['Research'] == []
    assert plan.deps['Qualify'] == ['Research']
    assert plan.deps['CRM'] == ['Qualify']
    assert plan.deps['Manager'] == ['CRM']
    assert plan.dropped_edges == []


def test_plan_breaks_cycles():
    definition = WorkforceDefinition(
        objective='x',
        agents=[agent('A'), agent('B')],
        workflows=[
            WorkflowEdge(from_agent='A', to_agent='B'),
            WorkflowEdge(from_agent='B', to_agent='A'),  # back-edge
        ],
    )
    plan = build_execution_plan(definition)
    assert plan.deps['B'] == ['A']
    assert plan.deps['A'] == []
    assert plan.dropped_edges == ['B->A']


def test_plan_collects_approval_targets():
    definition = WorkforceDefinition(
        objective='x',
        agents=[agent('A'), agent('B')],
        workflows=[
            WorkflowEdge(from_agent='A', to_agent='B', requires_approval=True)
        ],
    )
    assert build_execution_plan(definition).approval_required == ['B']


# ---------------------------------------------------------------------------
# Autonomous execution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_autonomous_chain(runtime, gateway):
    run = await runtime.start_run(chain_definition(), user_id='u1')

    # Only the entry agent launches at start.
    assert gateway.launched_names() == ['Research']

    await finish(runtime, gateway, 'Research')
    assert gateway.launched_names() == ['Research', 'Qualify']

    # Context flows forward: Qualify's kickoff embeds Research's output.
    qualify_kickoff = gateway.launches[1][1]
    assert 'output of Research' in qualify_kickoff

    await finish(runtime, gateway, 'Qualify')
    await finish(runtime, gateway, 'CRM')
    await finish(runtime, gateway, 'Manager')

    # All graph tasks done → aggregation (coordinator = Manager) launches.
    assert gateway.launched_names()[-1] == 'Manager'
    assert len(gateway.launches) == 5
    aggregation_kickoff = gateway.launches[-1][1]
    assert 'output of CRM' in aggregation_kickoff
    assert 'final deliverable' in aggregation_kickoff

    await finish(runtime, gateway, 'Manager', occurrence=1)

    final = await runtime.store.get_run_any_user(run.id)
    assert final.status == WorkflowRunStatus.COMPLETED
    assert final.final_output == 'output of Manager'
    kinds = [e.kind for e in await runtime.store.get_events(run.id)]
    assert kinds[0] == WorkflowEventKind.WORKFLOW_STARTED
    assert kinds[-1] == WorkflowEventKind.WORKFLOW_COMPLETED


@pytest.mark.asyncio
async def test_and_join_waits_for_all_upstreams(runtime, gateway):
    definition = WorkforceDefinition(
        objective='x',
        agents=[agent('A'), agent('B'), agent('C')],
        workflows=[
            WorkflowEdge(from_agent='A', to_agent='C'),
            WorkflowEdge(from_agent='B', to_agent='C'),
        ],
    )
    await runtime.start_run(definition)
    assert sorted(gateway.launched_names()) == ['A', 'B']

    await finish(runtime, gateway, 'A')
    assert 'C' not in gateway.launched_names()  # still waiting on B

    await finish(runtime, gateway, 'B')
    assert 'C' in gateway.launched_names()
    kickoff = gateway.launches[-1][1]
    assert 'output of A' in kickoff and 'output of B' in kickoff


@pytest.mark.asyncio
async def test_retry_then_success(runtime, gateway):
    definition = WorkforceDefinition(
        objective='x', agents=[agent('A')], workflows=[]
    )
    run = await runtime.start_run(definition)
    await finish(runtime, gateway, 'A', success=False)

    # Automatic retry relaunched A.
    assert gateway.launched_names().count('A') == 2
    tasks = await runtime.store.get_tasks(run.id)
    assert tasks[0].attempts == 2

    await finish(runtime, gateway, 'A', occurrence=1)
    await finish(runtime, gateway, SUPERVISOR_AGENT_NAME)
    final = await runtime.store.get_run_any_user(run.id)
    assert final.status == WorkflowRunStatus.COMPLETED


@pytest.mark.asyncio
async def test_retry_exhaustion_fails_run_and_manual_retry_revives(
    runtime, gateway
):
    definition = WorkforceDefinition(
        objective='x', agents=[agent('A')], workflows=[]
    )
    run = await runtime.start_run(definition)
    await finish(runtime, gateway, 'A', success=False)
    await finish(runtime, gateway, 'A', occurrence=1, success=False)

    failed = await runtime.store.get_run_any_user(run.id)
    assert failed.status == WorkflowRunStatus.FAILED
    task = (await runtime.store.get_tasks(run.id))[0]
    assert task.status == WorkflowTaskStatus.FAILED

    # Manual retry revives both the task and the run.
    await runtime.retry_task(run.id, task.id)
    revived = await runtime.store.get_run_any_user(run.id)
    assert revived.status == WorkflowRunStatus.RUNNING
    assert gateway.launched_names().count('A') == 3


@pytest.mark.asyncio
async def test_pause_blocks_handoffs_and_resume_continues(runtime, gateway):
    definition = WorkforceDefinition(
        objective='x',
        agents=[agent('A'), agent('B')],
        workflows=[WorkflowEdge(from_agent='A', to_agent='B')],
    )
    run = await runtime.start_run(definition, user_id=None)
    await runtime.pause(run.id)

    await finish(runtime, gateway, 'A')
    # Completion is recorded, but B must not launch while paused.
    assert 'B' not in gateway.launched_names()

    await runtime.resume(run.id)
    assert 'B' in gateway.launched_names()


@pytest.mark.asyncio
async def test_cancel_stops_queued_tasks(runtime, gateway):
    definition = WorkforceDefinition(
        objective='x',
        agents=[agent('A'), agent('B')],
        workflows=[WorkflowEdge(from_agent='A', to_agent='B')],
    )
    run = await runtime.start_run(definition)
    await runtime.cancel(run.id)

    cancelled = await runtime.store.get_run_any_user(run.id)
    assert cancelled.status == WorkflowRunStatus.CANCELLED
    statuses = {
        t.agent_name: t.status for t in await runtime.store.get_tasks(run.id)
    }
    assert statuses['B'] == WorkflowTaskStatus.CANCELLED

    # A late completion of the already-running A does not restart anything.
    await finish(runtime, gateway, 'A')
    assert 'B' not in gateway.launched_names()


@pytest.mark.asyncio
async def test_approval_gate_pauses_then_continues(runtime, gateway):
    definition = WorkforceDefinition(
        objective='x',
        agents=[agent('A'), agent('B')],
        workflows=[
            WorkflowEdge(from_agent='A', to_agent='B', requires_approval=True)
        ],
    )
    run = await runtime.start_run(definition)
    await finish(runtime, gateway, 'A')

    tasks = {t.agent_name: t for t in await runtime.store.get_tasks(run.id)}
    assert tasks['B'].status == WorkflowTaskStatus.WAITING_APPROVAL
    assert 'B' not in gateway.launched_names()
    kinds = [e.kind for e in await runtime.store.get_events(run.id)]
    assert WorkflowEventKind.APPROVAL_REQUIRED in kinds

    await runtime.approve_task(run.id, tasks['B'].id)
    assert 'B' in gateway.launched_names()


@pytest.mark.asyncio
async def test_launch_failure_is_retried_then_fails_run(runtime, gateway):
    gateway.fail_launch_for.add('A')
    definition = WorkforceDefinition(
        objective='x', agents=[agent('A')], workflows=[]
    )
    run = await runtime.start_run(definition)
    failed = await runtime.store.get_run_any_user(run.id)
    assert failed.status == WorkflowRunStatus.FAILED
    task = (await runtime.store.get_tasks(run.id))[0]
    assert task.attempts == task.max_attempts


@pytest.mark.asyncio
async def test_timeout_fails_stuck_task(runtime, gateway):
    definition = WorkforceDefinition(
        objective='x', agents=[agent('A')], workflows=[]
    )
    run = await runtime.start_run(definition)

    later = datetime.now(timezone.utc) + timedelta(hours=3)
    await runtime.check_timeouts(now=later)
    # First timeout consumes attempt 1 and requeues+relaunches; time out again.
    await runtime.check_timeouts(now=later + timedelta(hours=3))

    final = await runtime.store.get_run_any_user(run.id)
    assert final.status == WorkflowRunStatus.FAILED
    kinds = [e.kind for e in await runtime.store.get_events(run.id)]
    assert WorkflowEventKind.AGENT_TIMEOUT in kinds


@pytest.mark.asyncio
async def test_synthetic_supervisor_when_no_coordinator(runtime, gateway):
    definition = WorkforceDefinition(
        objective='x', agents=[agent('A')], workflows=[]
    )
    run = await runtime.start_run(definition)
    await finish(runtime, gateway, 'A')

    assert gateway.launched_names() == ['A', SUPERVISOR_AGENT_NAME]
    await finish(runtime, gateway, SUPERVISOR_AGENT_NAME)
    final = await runtime.store.get_run_any_user(run.id)
    assert final.status == WorkflowRunStatus.COMPLETED
    assert final.final_output == f'output of {SUPERVISOR_AGENT_NAME}'


class FakeActionExecutor:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    async def execute_action(self, run, agent_name, provider, tool, params):
        self.calls.append((agent_name, provider, tool, params))
        return (not self.fail, 'boom' if self.fail else None)


@pytest.mark.asyncio
async def test_edge_actions_fire_with_templated_params(async_session, gateway):
    from waspid.app_server.workforce.workforce_models import WorkflowAction

    actions = FakeActionExecutor()
    runtime = WorkflowRuntime(
        store=WorkflowRunStore(db_session=async_session),
        gateway=gateway,
        action_executor=actions,
    )
    definition = WorkforceDefinition(
        objective='Sell houses',
        agents=[agent('Research'), agent('CRM')],
        workflows=[
            WorkflowEdge(
                from_agent='Research',
                to_agent='CRM',
                actions=[
                    WorkflowAction(
                        provider='slack',
                        tool='send_message',
                        params={
                            'channel': '#sales',
                            'text': 'Done: {{output}} ({{objective}})',
                        },
                    )
                ],
            )
        ],
    )
    run = await runtime.start_run(definition)
    await finish(runtime, gateway, 'Research')

    assert actions.calls == [
        (
            'Research',
            'slack',
            'send_message',
            {'channel': '#sales', 'text': 'Done: output of Research (Sell houses)'},
        )
    ]
    kinds = [e.kind for e in await runtime.store.get_events(run.id)]
    assert WorkflowEventKind.ACTION_EXECUTED in kinds
    # The handoff still happened.
    assert 'CRM' in gateway.launched_names()


@pytest.mark.asyncio
async def test_failed_action_logs_event_but_run_continues(async_session, gateway):
    from waspid.app_server.workforce.workforce_models import WorkflowAction

    actions = FakeActionExecutor(fail=True)
    runtime = WorkflowRuntime(
        store=WorkflowRunStore(db_session=async_session),
        gateway=gateway,
        action_executor=actions,
    )
    definition = WorkforceDefinition(
        objective='x',
        agents=[agent('A'), agent('B')],
        workflows=[
            WorkflowEdge(
                from_agent='A',
                to_agent='B',
                actions=[
                    WorkflowAction(provider='slack', tool='send_message', params={})
                ],
            )
        ],
    )
    run = await runtime.start_run(definition)
    await finish(runtime, gateway, 'A')

    kinds = [e.kind for e in await runtime.store.get_events(run.id)]
    assert WorkflowEventKind.ACTION_FAILED in kinds
    assert 'B' in gateway.launched_names()  # action failure does not block
    current = await runtime.store.get_run_any_user(run.id)
    assert current.status == WorkflowRunStatus.RUNNING


@pytest.mark.asyncio
async def test_unknown_conversation_is_ignored(runtime, gateway):
    definition = WorkforceDefinition(
        objective='x', agents=[agent('A')], workflows=[]
    )
    await runtime.start_run(definition)
    await runtime.handle_agent_finished(uuid4(), success=True)  # no crash
    assert gateway.launched_names() == ['A']
