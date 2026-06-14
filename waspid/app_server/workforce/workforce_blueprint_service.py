# Waspid AI OS
"""SQL-backed store for workforce blueprints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from waspid.app_server.utils.sql_utils import (
    Base,
    UtcDateTime,
    create_json_type_decorator,
    row2dict,
)
from waspid.app_server.workforce.workforce_models import (
    WorkforceBlueprint,
    WorkforceDefinition,
)


class StoredWorkforceBlueprint(Base):
    __tablename__ = 'workforce_blueprint'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    definition: Mapped[WorkforceDefinition] = mapped_column(
        create_json_type_decorator(WorkforceDefinition)
    )
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, server_default=func.now(), onupdate=func.now()
    )


@dataclass
class WorkforceBlueprintService:
    """CRUD for blueprints, scoped to one user.

    ``user_id`` may be None on single-user (OSS) deployments; rows are
    then stored and matched with a NULL user_id.
    """

    db_session: AsyncSession
    user_id: str | None = None

    async def create(
        self, name: str, definition: WorkforceDefinition
    ) -> WorkforceBlueprint:
        blueprint = WorkforceBlueprint(
            id=uuid4(), user_id=self.user_id, name=name, definition=definition
        )
        stored = StoredWorkforceBlueprint(
            id=blueprint.id,
            user_id=blueprint.user_id,
            name=blueprint.name,
            definition=blueprint.definition,
        )
        self.db_session.add(stored)
        await self.db_session.commit()
        await self.db_session.refresh(stored)
        return WorkforceBlueprint.model_validate(row2dict(stored))

    async def get(self, blueprint_id: UUID) -> WorkforceBlueprint | None:
        stored = await self._get_stored(blueprint_id)
        if stored is None:
            return None
        return WorkforceBlueprint.model_validate(row2dict(stored))

    async def list(self) -> list[WorkforceBlueprint]:
        stmt = (
            select(StoredWorkforceBlueprint)
            .where(StoredWorkforceBlueprint.user_id == self.user_id)
            .order_by(StoredWorkforceBlueprint.created_at.desc())
        )
        result = await self.db_session.execute(stmt)
        return [
            WorkforceBlueprint.model_validate(row2dict(row))
            for row in result.scalars()
        ]

    async def delete(self, blueprint_id: UUID) -> bool:
        stored = await self._get_stored(blueprint_id)
        if stored is None:
            return False
        await self.db_session.delete(stored)
        await self.db_session.commit()
        return True

    async def clone(self, blueprint_id: UUID) -> WorkforceBlueprint | None:
        source = await self.get(blueprint_id)
        if source is None:
            return None
        return await self.create(f'{source.name} (copy)', source.definition)

    async def _get_stored(
        self, blueprint_id: UUID
    ) -> StoredWorkforceBlueprint | None:
        stmt = select(StoredWorkforceBlueprint).where(
            StoredWorkforceBlueprint.id == blueprint_id,
            StoredWorkforceBlueprint.user_id == self.user_id,
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()
