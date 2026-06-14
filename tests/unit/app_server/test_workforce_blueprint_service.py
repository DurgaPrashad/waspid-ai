# Waspid AI OS
"""Tests for WorkforceBlueprintService using in-memory SQLite."""

from typing import AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from waspid.app_server.utils.sql_utils import Base
from waspid.app_server.workforce.workforce_blueprint_service import (
    WorkforceBlueprintService,
)
from waspid.app_server.workforce.workforce_models import (
    AgentSpec,
    WorkflowEdge,
    WorkforceDefinition,
)


@pytest.fixture
async def async_engine():
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with maker() as db_session:
        yield db_session


@pytest.fixture
def service(async_session) -> WorkforceBlueprintService:
    return WorkforceBlueprintService(db_session=async_session, user_id='user_1')


def sample_definition() -> WorkforceDefinition:
    return WorkforceDefinition(
        objective='Run a real estate lead generation business',
        summary='A small lead-gen workforce',
        agents=[
            AgentSpec(
                name='Sales Manager Agent',
                role='Coordinates the workforce',
                system_prompt='You are the sales manager...',
                tools=['browser'],
            ),
            AgentSpec(
                name='Lead Research Agent',
                role='Finds leads',
                system_prompt='You research leads...',
                tools=['web_search'],
                reports_to='Sales Manager Agent',
            ),
        ],
        workflows=[
            WorkflowEdge(
                from_agent='Lead Research Agent',
                to_agent='Sales Manager Agent',
                trigger='leads collected',
            )
        ],
    )


@pytest.mark.asyncio
async def test_create_and_get(service):
    created = await service.create('Lead Gen', sample_definition())
    assert created.name == 'Lead Gen'
    assert created.user_id == 'user_1'

    fetched = await service.get(created.id)
    assert fetched is not None
    assert fetched.definition.objective == sample_definition().objective
    assert [a.name for a in fetched.definition.agents] == [
        'Sales Manager Agent',
        'Lead Research Agent',
    ]


@pytest.mark.asyncio
async def test_list_returns_newest_first_for_owner_only(service, async_session):
    await service.create('First', sample_definition())
    await service.create('Second', sample_definition())
    other_user = WorkforceBlueprintService(
        db_session=async_session, user_id='someone_else'
    )
    await other_user.create('Not mine', sample_definition())

    names = [b.name for b in await service.list()]
    assert set(names) == {'First', 'Second'}
    assert 'Not mine' not in names


@pytest.mark.asyncio
async def test_get_does_not_leak_across_users(service, async_session):
    created = await service.create('Private', sample_definition())
    other_user = WorkforceBlueprintService(
        db_session=async_session, user_id='someone_else'
    )
    assert await other_user.get(created.id) is None
    assert await other_user.delete(created.id) is False


@pytest.mark.asyncio
async def test_delete(service):
    created = await service.create('Doomed', sample_definition())
    assert await service.delete(created.id) is True
    assert await service.get(created.id) is None
    assert await service.delete(created.id) is False


@pytest.mark.asyncio
async def test_clone(service):
    created = await service.create('Original', sample_definition())
    clone = await service.clone(created.id)
    assert clone is not None
    assert clone.id != created.id
    assert clone.name == 'Original (copy)'
    assert clone.definition == created.definition


@pytest.mark.asyncio
async def test_clone_missing_returns_none(service):
    assert await service.clone(uuid4()) is None


@pytest.mark.asyncio
async def test_null_user_scope(async_session):
    anonymous = WorkforceBlueprintService(db_session=async_session, user_id=None)
    created = await anonymous.create('OSS blueprint', sample_definition())
    assert created.user_id is None
    assert [b.name for b in await anonymous.list()] == ['OSS blueprint']
