# pyright: reportIncompatibleMethodOverride=false
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Literal
from uuid import UUID, uuid4

from pydantic import Field

from waspid.agent_server.utils import WaspidUUID, utc_now
from waspid.app_server.event_callback.event_callback_result_models import (
    EventCallbackResult,
    EventCallbackResultStatus,
)
from waspid.sdk import Event
from waspid.sdk.utils.models import (
    DiscriminatedUnionMixin,
    WaspidModel,
    get_known_concrete_subclasses,
)
from waspid.sdk.utils.redact import redact_text_secrets

_logger = logging.getLogger(__name__)
if TYPE_CHECKING:
    EventKind = str
else:
    EventKind = Literal[tuple(c.__name__ for c in get_known_concrete_subclasses(Event))]


class EventCallbackStatus(Enum):
    ACTIVE = 'ACTIVE'
    DISABLED = 'DISABLED'
    COMPLETED = 'COMPLETED'
    ERROR = 'ERROR'


class EventCallbackProcessor(DiscriminatedUnionMixin, ABC):
    @abstractmethod
    async def __call__(
        self,
        conversation_id: UUID,
        callback: EventCallback,
        event: Event,
    ) -> EventCallbackResult | None:
        """Process an event."""


class LoggingCallbackProcessor(EventCallbackProcessor):
    """Example implementation which logs callbacks."""

    async def __call__(
        self,
        conversation_id: UUID,
        callback: EventCallback,
        event: Event,
    ) -> EventCallbackResult:
        _logger.info(
            'Callback %s Invoked for event %s',
            callback.id,
            redact_text_secrets(str(event)),
        )
        return EventCallbackResult(
            status=EventCallbackResultStatus.SUCCESS,
            event_callback_id=callback.id,
            event_id=event.id,
            conversation_id=conversation_id,
        )


class CreateEventCallbackRequest(WaspidModel):
    conversation_id: WaspidUUID | None = Field(
        default=None,
        description=(
            'Optional filter on the conversation to which this callback applies'
        ),
    )
    processor: EventCallbackProcessor
    event_kind: EventKind | None = Field(
        default=None,
        description=(
            'Optional filter on the type of events to which this callback applies'
        ),
    )


class EventCallback(CreateEventCallbackRequest):
    id: WaspidUUID = Field(default_factory=uuid4)
    status: EventCallbackStatus = Field(default=EventCallbackStatus.ACTIVE)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class EventCallbackPage(WaspidModel):
    items: list[EventCallback]
    next_page_id: str | None = None
