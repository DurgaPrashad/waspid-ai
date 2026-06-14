# Waspid AI OS
"""Security tests: SSRF guard, rate limits, size caps, tenant isolation."""

from typing import AsyncGenerator

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# Imported at module level so the stored models register with Base
# before the fixture's create_all runs.
from waspid.app_server.integrations_hub.hub_service import (
    IntegrationHubService,
)
from waspid.app_server.integrations_hub.tool_executors import execute_tool
from waspid.app_server.integrations_hub.url_guard import (
    UnsafeUrlError,
    validate_outbound_url,
)
from waspid.app_server.utils.sql_utils import Base
from waspid.app_server.utils.user_rate_limit import UserRateLimiter
from waspid.app_server.workforce.workflow_models import (
    WorkflowRunStatus,
)
from waspid.app_server.workforce.workflow_run_service import WorkflowRunStore
from waspid.app_server.workforce.workforce_models import (
    AgentSpec,
    WorkforceDefinition,
)

# ---------------------------------------------------------------------------
# SSRF guard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'url',
    [
        'http://example.com/hook',  # not https
        'https://localhost/hook',
        'https://127.0.0.1/hook',
        'https://10.0.0.5/hook',
        'https://192.168.1.1/hook',
        'https://172.16.0.1/hook',
        'https://169.254.169.254/latest/meta-data/',  # cloud metadata
        'https://metadata.google.internal/computeMetadata/v1/',
        'https://[::1]/hook',
        'not a url at all',
    ],
)
def test_unsafe_urls_rejected(url):
    with pytest.raises(UnsafeUrlError):
        validate_outbound_url(url)


def test_public_https_url_allowed():
    # discord.com resolves publicly; if offline, the resolver error is
    # also a rejection, so assert only that public https CAN pass by
    # checking a literal public IP (no DNS needed).
    validate_outbound_url('https://8.8.8.8/hook')


@pytest.mark.asyncio
async def test_webhook_executor_refuses_internal_target():
    called = False

    def handler(request):
        nonlocal called
        called = True
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await execute_tool(
            client,
            'webhook',
            'post',
            'https://169.254.169.254/latest/meta-data/',
            None,
            {'payload_json': '{}'},
        )
    assert not result.ok
    assert 'unsafe webhook URL' in result.error
    assert called is False  # request was never sent


@pytest.mark.asyncio
async def test_discord_executor_refuses_http_target():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200))
    ) as client:
        result = await execute_tool(
            client, 'discord', 'send_message', 'http://example.com/wh', None,
            {'text': 'hi'},
        )
    assert not result.ok


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------


def test_rate_limiter_caps_and_recovers():
    limiter = UserRateLimiter(max_requests=3, window_seconds=60)
    assert all(limiter.allow('u1', now=t) for t in (0.0, 1.0, 2.0))
    assert limiter.allow('u1', now=3.0) is False
    # Another user is unaffected.
    assert limiter.allow('u2', now=3.0) is True
    # Window slides: after 61s the first requests expire.
    assert limiter.allow('u1', now=61.5) is True


# ---------------------------------------------------------------------------
# Definition size caps
# ---------------------------------------------------------------------------


def _agent(i: int) -> dict:
    return {'name': f'A{i}', 'role': 'r', 'system_prompt': 'p'}


def test_definition_rejects_more_than_100_agents():
    with pytest.raises(ValidationError):
        WorkforceDefinition(
            objective='x', agents=[_agent(i) for i in range(101)]
        )


def test_agent_rejects_oversized_prompt():
    with pytest.raises(ValidationError):
        AgentSpec(name='A', role='r', system_prompt='x' * 20001)


def test_definition_at_limit_is_accepted():
    definition = WorkforceDefinition(
        objective='x', agents=[_agent(i) for i in range(100)]
    )
    assert len(definition.agents) == 100


# ---------------------------------------------------------------------------
# Tenant isolation: workflow runs
# ---------------------------------------------------------------------------


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


@pytest.mark.asyncio
async def test_workflow_runs_are_tenant_isolated(async_session):
    from waspid.app_server.workforce.workflow_models import WorkflowRun

    org_a = WorkflowRunStore(db_session=async_session, user_id='org-a-user')
    org_b = WorkflowRunStore(db_session=async_session, user_id='org-b-user')

    definition = WorkforceDefinition(objective='x', agents=[_agent(0)])
    run = await org_a.create_run(
        WorkflowRun(user_id='org-a-user', name='secret run', definition=definition)
    )

    # Org B cannot see, fetch, or (via the router's ownership check)
    # control org A's run.
    assert await org_b.list_runs() == []
    assert await org_b.get_run(run.id) is None
    assert (await org_a.get_run(run.id)).status == WorkflowRunStatus.RUNNING


@pytest.mark.asyncio
async def test_tool_call_logs_are_tenant_isolated(async_session, monkeypatch):
    import sys
    import types

    # Stub credential encryption (same approach as test_integration_hub).
    class FakeJwtService:
        def create_jwe_token(self, payload):
            return 'enc:' + payload['v']

        def decrypt_jwe_token(self, token):
            return {'v': token[4:]}

    class FakeJwtInjector:
        def get_jwt_service(self):
            return FakeJwtService()

    class FakeGlobalConfig:
        jwt = FakeJwtInjector()

    fake_config = types.ModuleType('waspid.app_server.config')
    fake_config.get_global_config = lambda: FakeGlobalConfig()
    monkeypatch.setitem(sys.modules, 'waspid.app_server.config', fake_config)

    from pydantic import SecretStr

    org_a = IntegrationHubService(db_session=async_session, user_id='org-a-user')
    org_b = IntegrationHubService(db_session=async_session, user_id='org-b-user')
    await org_a.create_connection('slack', SecretStr('xoxb-a'))

    def handler(request):
        return httpx.Response(200, json={'ok': True})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await org_a.execute(
            client, 'slack', 'send_message', {'channel': '#a', 'text': 'hi'}
        )

    assert (await org_b.recent_calls()) == []
    assert (await org_b.stats()).total == 0
    assert (await org_a.stats()).total == 1
