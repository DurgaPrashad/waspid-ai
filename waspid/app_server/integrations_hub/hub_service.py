# Waspid AI OS
"""Connection store, tool-call log, and execution orchestration."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

import httpx
from pydantic import SecretStr
from sqlalchemy import Boolean, Integer, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from waspid.app_server.integrations_hub.hub_models import (
    INTEGRATION_REGISTRY,
    IntegrationConnection,
    ToolCallLogEntry,
    ToolCallResult,
    ToolCallStats,
)
from waspid.app_server.integrations_hub.tool_executors import (
    HEALTH_CHECKS,
    execute_tool,
)
from waspid.app_server.utils.sql_utils import (
    Base,
    StoredSecretStr,
    UtcDateTime,
    row2dict,
)


class StoredIntegrationConnection(Base):
    __tablename__ = 'integration_connection'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, default='')
    credential: Mapped[SecretStr] = mapped_column(StoredSecretStr, nullable=False)
    base_url: Mapped[str | None] = mapped_column(String, nullable=True)
    last_check_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    last_check_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, server_default=func.now()
    )


class StoredToolCallLog(Base):
    __tablename__ = 'tool_call_log'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String, nullable=False, index=True)
    tool: Mapped[str] = mapped_column(String, nullable=False)
    ok: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    run_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    agent_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, server_default=func.now(), index=True
    )


def _connection_from_row(stored: StoredIntegrationConnection) -> IntegrationConnection:
    data = row2dict(stored)
    data.pop('credential', None)  # never expose credentials in responses
    return IntegrationConnection.model_validate(data)


def _secret_value(raw) -> str:
    """Decrypt a credential read from the database.

    ``StoredSecretStr`` encrypts on write, but SQLAlchemy result
    processing returns the raw JWE token (the upstream decorator
    implements ``process_result_param``, which SQLAlchemy never calls),
    so decryption is done here explicitly. Tolerates both behaviors.
    """
    if hasattr(raw, 'get_secret_value'):
        return raw.get_secret_value()
    from waspid.app_server.config import get_global_config

    jwt_injector = get_global_config().jwt
    assert jwt_injector is not None
    return jwt_injector.get_jwt_service().decrypt_jwe_token(raw)['v']


@dataclass
class IntegrationHubService:
    db_session: AsyncSession
    user_id: str | None = None

    # -- connections -------------------------------------------------------

    async def create_connection(
        self,
        provider: str,
        credential: SecretStr,
        name: str = '',
        base_url: str | None = None,
    ) -> IntegrationConnection:
        # One connection per provider per user: replace existing.
        existing = await self._get_stored_by_provider(provider)
        if existing is not None:
            await self.db_session.delete(existing)
        connection = IntegrationConnection(
            user_id=self.user_id, provider=provider, name=name, base_url=base_url
        )
        self.db_session.add(
            StoredIntegrationConnection(
                id=connection.id,
                user_id=self.user_id,
                provider=provider,
                name=name,
                credential=credential,
                base_url=base_url,
            )
        )
        await self.db_session.commit()
        return connection

    async def list_connections(self) -> list[IntegrationConnection]:
        stmt = (
            select(StoredIntegrationConnection)
            .where(StoredIntegrationConnection.user_id == self.user_id)
            .order_by(StoredIntegrationConnection.created_at)
        )
        result = await self.db_session.execute(stmt)
        return [_connection_from_row(row) for row in result.scalars()]

    async def delete_connection(self, connection_id: UUID) -> bool:
        stmt = select(StoredIntegrationConnection).where(
            StoredIntegrationConnection.id == connection_id,
            StoredIntegrationConnection.user_id == self.user_id,
        )
        result = await self.db_session.execute(stmt)
        stored = result.scalar_one_or_none()
        if stored is None:
            return False
        await self.db_session.delete(stored)
        await self.db_session.commit()
        return True

    async def get_credential(self, provider: str) -> tuple[str, str | None] | None:
        """Return (credential, base_url) for the user's connection."""
        stored = await self._get_stored_by_provider(provider)
        if stored is None:
            return None
        return _secret_value(stored.credential), stored.base_url

    # -- execution ---------------------------------------------------------

    async def execute(
        self,
        client: httpx.AsyncClient,
        provider: str,
        tool: str,
        params: dict[str, str],
        run_id: UUID | None = None,
        agent_name: str | None = None,
    ) -> ToolCallResult:
        creds = await self.get_credential(provider)
        if creds is None:
            result = ToolCallResult(
                ok=False, error=f'no connection for provider: {provider}'
            )
            await self._log(provider, tool, result, 0, run_id, agent_name)
            return result
        credential, base_url = creds
        started = time.monotonic()
        result = await execute_tool(client, provider, tool, credential, base_url, params)
        latency_ms = int((time.monotonic() - started) * 1000)
        await self._log(provider, tool, result, latency_ms, run_id, agent_name)
        return result

    async def check_connection(
        self, client: httpx.AsyncClient, connection_id: UUID
    ) -> IntegrationConnection | None:
        stmt = select(StoredIntegrationConnection).where(
            StoredIntegrationConnection.id == connection_id,
            StoredIntegrationConnection.user_id == self.user_id,
        )
        result = await self.db_session.execute(stmt)
        stored = result.scalar_one_or_none()
        if stored is None:
            return None
        check = HEALTH_CHECKS.get(stored.provider)
        if check is not None:
            outcome = await check(
                client, _secret_value(stored.credential), stored.base_url
            )
            stored.last_check_ok = outcome.ok
        else:
            # No remote check implemented: credential presence is the check.
            stored.last_check_ok = bool(_secret_value(stored.credential))
        stored.last_check_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(stored)
        return _connection_from_row(stored)

    # -- observability -------------------------------------------------------

    async def recent_calls(self, limit: int = 50) -> list[ToolCallLogEntry]:
        stmt = (
            select(StoredToolCallLog)
            .where(StoredToolCallLog.user_id == self.user_id)
            .order_by(StoredToolCallLog.created_at.desc())
            .limit(limit)
        )
        result = await self.db_session.execute(stmt)
        return [
            ToolCallLogEntry.model_validate(row2dict(row))
            for row in result.scalars()
        ]

    async def stats(self) -> ToolCallStats:
        stmt = select(
            func.count(StoredToolCallLog.id),
            func.sum(func.cast(~StoredToolCallLog.ok, Integer)),
            func.avg(StoredToolCallLog.latency_ms),
        ).where(StoredToolCallLog.user_id == self.user_id)
        total, failures, avg_latency = (await self.db_session.execute(stmt)).one()
        return ToolCallStats(
            total=total or 0,
            failures=failures or 0,
            avg_latency_ms=float(avg_latency) if avg_latency is not None else None,
        )

    # -- internals ---------------------------------------------------------

    async def _get_stored_by_provider(
        self, provider: str
    ) -> StoredIntegrationConnection | None:
        if provider not in INTEGRATION_REGISTRY:
            return None
        stmt = select(StoredIntegrationConnection).where(
            StoredIntegrationConnection.provider == provider,
            StoredIntegrationConnection.user_id == self.user_id,
        )
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def _log(
        self,
        provider: str,
        tool: str,
        result: ToolCallResult,
        latency_ms: int,
        run_id: UUID | None,
        agent_name: str | None,
    ) -> None:
        entry = ToolCallLogEntry(
            user_id=self.user_id,
            provider=provider,
            tool=tool,
            ok=result.ok,
            status_code=result.status_code,
            error=result.error,
            latency_ms=latency_ms,
            run_id=run_id,
            agent_name=agent_name,
        )
        self.db_session.add(
            StoredToolCallLog(
                id=entry.id,
                user_id=entry.user_id,
                provider=entry.provider,
                tool=entry.tool,
                ok=entry.ok,
                status_code=entry.status_code,
                error=entry.error,
                latency_ms=entry.latency_ms,
                run_id=entry.run_id,
                agent_name=entry.agent_name,
                # Explicit timestamp: sub-second precision so the log
                # orders deterministically (SQLite CURRENT_TIMESTAMP is
                # second-resolution).
                created_at=datetime.now(timezone.utc),
            )
        )
        await self.db_session.commit()
