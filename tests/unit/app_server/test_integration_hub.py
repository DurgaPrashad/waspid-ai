# Waspid AI OS
"""Tests for the Integration Hub: executors (mocked HTTP) and the service."""

import json
from typing import AsyncGenerator
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from waspid.app_server.integrations_hub.hub_models import INTEGRATION_REGISTRY
from waspid.app_server.integrations_hub.hub_service import IntegrationHubService
from waspid.app_server.integrations_hub.tool_executors import execute_tool
from waspid.app_server.utils.sql_utils import Base


def make_client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.fixture(autouse=True)
def fake_credential_encryption(monkeypatch):
    """Stub the JWE credential encryption used by StoredSecretStr.

    The real implementation pulls the JWT service out of the global app
    config; unit tests substitute a reversible fake so connection rows
    can round-trip without a configured server.
    """
    import sys
    import types

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
def service(async_session) -> IntegrationHubService:
    return IntegrationHubService(db_session=async_session, user_id='u1')


# ---------------------------------------------------------------------------
# Registry sanity
# ---------------------------------------------------------------------------


def test_registry_covers_required_categories():
    categories = {spec.category for spec in INTEGRATION_REGISTRY.values()}
    assert {'communication', 'crm', 'development', 'documents'} <= categories
    for required in ('slack', 'github', 'gitlab', 'hubspot', 'salesforce',
                     'pipedrive', 'notion', 'jira', 'linear', 'discord',
                     'google_workspace', 'microsoft365', 'webhook'):
        assert required in INTEGRATION_REGISTRY


# ---------------------------------------------------------------------------
# Executors (HTTP mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slack_send_message_success():
    def handler(request):
        assert request.url.path == '/api/chat.postMessage'
        assert request.headers['Authorization'] == 'Bearer xoxb-test'
        body = json.loads(request.content)
        assert body == {'channel': '#sales', 'text': 'lead qualified'}
        return httpx.Response(200, json={'ok': True, 'ts': '1'})

    async with make_client(handler) as client:
        result = await execute_tool(
            client, 'slack', 'send_message', 'xoxb-test', None,
            {'channel': '#sales', 'text': 'lead qualified'},
        )
    assert result.ok


@pytest.mark.asyncio
async def test_slack_api_level_error_is_failure():
    def handler(request):
        return httpx.Response(200, json={'ok': False, 'error': 'invalid_auth'})

    async with make_client(handler) as client:
        result = await execute_tool(
            client, 'slack', 'send_message', 'bad', None,
            {'channel': '#x', 'text': 'y'},
        )
    assert not result.ok


@pytest.mark.asyncio
async def test_github_create_issue():
    def handler(request):
        assert request.url.path == '/repos/acme/site/issues'
        return httpx.Response(201, json={'number': 7})

    async with make_client(handler) as client:
        result = await execute_tool(
            client, 'github', 'create_issue', 'ghp_x', None,
            {'repo': 'acme/site', 'title': 'Bug'},
        )
    assert result.ok
    assert result.data['number'] == 7


@pytest.mark.asyncio
async def test_hubspot_create_contact():
    def handler(request):
        body = json.loads(request.content)
        assert body['properties']['email'] == 'lead@example.com'
        return httpx.Response(201, json={'id': '101'})

    async with make_client(handler) as client:
        result = await execute_tool(
            client, 'hubspot', 'create_contact', 'pat-x', None,
            {'email': 'lead@example.com', 'firstname': 'Lee'},
        )
    assert result.ok


@pytest.mark.asyncio
async def test_missing_required_params_rejected_without_http():
    async with make_client(lambda r: httpx.Response(500)) as client:
        result = await execute_tool(
            client, 'slack', 'send_message', 'tok', None, {'channel': '#x'}
        )
    assert not result.ok
    assert 'missing params' in result.error


@pytest.mark.asyncio
async def test_sandbox_tools_refuse_server_execution():
    async with make_client(lambda r: httpx.Response(200)) as client:
        result = await execute_tool(
            client, 'pipedrive', 'manage_deals', 'tok', None, {}
        )
    assert not result.ok
    assert 'sandbox' in result.error


@pytest.mark.asyncio
async def test_unknown_provider_and_tool():
    async with make_client(lambda r: httpx.Response(200)) as client:
        assert not (await execute_tool(client, 'nope', 'x', 't', None, {})).ok
        assert not (await execute_tool(client, 'slack', 'nope', 't', None, {})).ok


# ---------------------------------------------------------------------------
# Service: connections, execution logging, stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connection_lifecycle(service):
    connection = await service.create_connection(
        'slack', SecretStr('xoxb-1'), name='Sales workspace'
    )
    assert connection.provider == 'slack'

    listed = await service.list_connections()
    assert [c.provider for c in listed] == ['slack']

    # Replacing the same provider keeps one connection.
    await service.create_connection('slack', SecretStr('xoxb-2'))
    assert len(await service.list_connections()) == 1
    credential, _ = await service.get_credential('slack')
    assert credential == 'xoxb-2'

    assert await service.delete_connection(listed[0].id) is False  # replaced id
    remaining = await service.list_connections()
    assert await service.delete_connection(remaining[0].id) is True
    assert await service.list_connections() == []


@pytest.mark.asyncio
async def test_connections_are_user_scoped(service, async_session):
    await service.create_connection('slack', SecretStr('xoxb-1'))
    other = IntegrationHubService(db_session=async_session, user_id='intruder')
    assert await other.list_connections() == []
    assert await other.get_credential('slack') is None


@pytest.mark.asyncio
async def test_execute_logs_success_and_failure(service):
    await service.create_connection('slack', SecretStr('xoxb-1'))

    def handler(request):
        return httpx.Response(200, json={'ok': True})

    async with make_client(handler) as client:
        result = await service.execute(
            client, 'slack', 'send_message',
            {'channel': '#x', 'text': 'hi'}, run_id=uuid4(), agent_name='CRM Agent',
        )
    assert result.ok

    # No connection for github -> failure, also logged.
    async with make_client(handler) as client:
        result = await service.execute(client, 'github', 'create_issue', {})
    assert not result.ok

    calls = await service.recent_calls()
    assert len(calls) == 2
    assert calls[0].provider == 'github' and not calls[0].ok
    assert calls[1].provider == 'slack' and calls[1].ok
    assert calls[1].agent_name == 'CRM Agent'

    stats = await service.stats()
    assert stats.total == 2
    assert stats.failures == 1


@pytest.mark.asyncio
async def test_health_check_updates_connection(service):
    await service.create_connection('slack', SecretStr('xoxb-1'))
    connection = (await service.list_connections())[0]

    def handler(request):
        assert request.url.path == '/api/auth.test'
        return httpx.Response(200, json={'ok': True})

    async with make_client(handler) as client:
        checked = await service.check_connection(client, connection.id)
    assert checked.last_check_ok is True
    assert checked.last_check_at is not None
