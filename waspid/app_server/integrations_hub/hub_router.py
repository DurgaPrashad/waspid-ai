# Waspid AI OS
"""Integration Hub router under /api/v1/integrations-hub."""

import logging
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from waspid.app_server.config import depends_db_session, depends_httpx_client
from waspid.app_server.integrations_hub.hub_models import (
    INTEGRATION_REGISTRY,
    CreateConnectionRequest,
    CredentialKind,
    ExecuteToolRequest,
    IntegrationConnection,
    ProviderStatus,
    ToolCallLogPage,
    ToolCallResult,
)
from waspid.app_server.integrations_hub.hub_service import IntegrationHubService
from waspid.app_server.integrations_hub.url_guard import (
    UnsafeUrlError,
    validate_outbound_url,
)
from waspid.app_server.user_auth import get_user_id
from waspid.app_server.utils.user_rate_limit import UserRateLimiter

_audit_logger = logging.getLogger('waspid.audit')

# Outbound tool execution is expensive (external API calls): cap per user.
_execute_rate_limit = UserRateLimiter(max_requests=30, window_seconds=60)

router = APIRouter(prefix='/integrations-hub', tags=['Integration Hub'])
db_session_dependency = depends_db_session()
httpx_client_dependency = depends_httpx_client()


def _service(
    db_session: Annotated[AsyncSession, db_session_dependency],
    user_id: Annotated[str | None, Depends(get_user_id)],
) -> IntegrationHubService:
    return IntegrationHubService(db_session=db_session, user_id=user_id)


@router.get('/providers')
async def list_providers(
    service: Annotated[IntegrationHubService, Depends(_service)],
) -> list[ProviderStatus]:
    """The tool registry, with the caller's connection state per provider."""
    connections = {c.provider: c for c in await service.list_connections()}
    return [
        ProviderStatus(spec=spec, connection=connections.get(spec.id))
        for spec in INTEGRATION_REGISTRY.values()
    ]


@router.post('/connections', status_code=status.HTTP_201_CREATED)
async def create_connection(
    request: CreateConnectionRequest,
    service: Annotated[IntegrationHubService, Depends(_service)],
    user_id: Annotated[str | None, Depends(get_user_id)],
) -> IntegrationConnection:
    if request.provider not in INTEGRATION_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Unknown provider: {request.provider}',
        )
    spec = INTEGRATION_REGISTRY[request.provider]
    if spec.base_url_required and not request.base_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'{spec.name} requires a base_url.',
        )
    if spec.credential_kind == CredentialKind.WEBHOOK_URL:
        try:
            validate_outbound_url(request.credential.get_secret_value())
        except UnsafeUrlError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Unsafe webhook URL: {exc}',
            )
    connection = await service.create_connection(
        request.provider, request.credential, request.name, request.base_url
    )
    _audit_logger.info(
        'integration_connection_created user=%s provider=%s connection=%s',
        user_id,
        request.provider,
        connection.id,
    )
    return connection


@router.get('/connections')
async def list_connections(
    service: Annotated[IntegrationHubService, Depends(_service)],
) -> list[IntegrationConnection]:
    return await service.list_connections()


@router.delete('/connections/{connection_id}')
async def delete_connection(
    connection_id: UUID,
    service: Annotated[IntegrationHubService, Depends(_service)],
    user_id: Annotated[str | None, Depends(get_user_id)],
) -> dict:
    if not await service.delete_connection(connection_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    _audit_logger.info(
        'integration_connection_deleted user=%s connection=%s',
        user_id,
        connection_id,
    )
    return {'success': True}


@router.post('/connections/{connection_id}/check')
async def check_connection(
    connection_id: UUID,
    service: Annotated[IntegrationHubService, Depends(_service)],
    httpx_client: Annotated[httpx.AsyncClient, httpx_client_dependency],
) -> IntegrationConnection:
    connection = await service.check_connection(httpx_client, connection_id)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return connection


@router.post('/tools/{provider}/{tool}/execute')
async def execute_tool(
    provider: str,
    tool: str,
    request: ExecuteToolRequest,
    service: Annotated[IntegrationHubService, Depends(_service)],
    httpx_client: Annotated[httpx.AsyncClient, httpx_client_dependency],
    user_id: Annotated[str | None, Depends(get_user_id)],
) -> ToolCallResult:
    """Execute a server-side tool with the caller's stored credential."""
    if not _execute_rate_limit.allow(user_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail='Tool execution rate limit reached; retry shortly.',
        )
    return await service.execute(httpx_client, provider, tool, request.params)


@router.get('/tool-calls')
async def list_tool_calls(
    service: Annotated[IntegrationHubService, Depends(_service)],
) -> ToolCallLogPage:
    return ToolCallLogPage(
        items=await service.recent_calls(), stats=await service.stats()
    )
