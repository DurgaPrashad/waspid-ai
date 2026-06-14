# Waspid AI OS
"""Production adapters wiring the workflow runtime to real Waspid runs.

- ``LiveAgentGateway`` launches workforce agents as app conversations
  (with the handoff processor attached) and reads their final messages.
- ``WorkflowHandoffProcessor`` is an event-callback processor invoked by
  the webhook pipeline whenever a launched conversation emits events;
  on a terminal execution status it advances the workflow — this is what
  makes hand-offs fire automatically.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from uuid import UUID, uuid4

from waspid.app_server.event_callback.event_callback_models import (
    EventCallback,
    EventCallbackProcessor,
    EventCallbackStatus,
)
from waspid.app_server.event_callback.event_callback_result_models import (
    EventCallbackResult,
    EventCallbackResultStatus,
)
from waspid.app_server.services.injector import InjectorState
from waspid.app_server.user.specifiy_user_context import (
    ADMIN,
    USER_CONTEXT_ATTR,
)
from waspid.app_server.workforce.workflow_models import (
    WorkflowRun,
    WorkflowTask,
)
from waspid.app_server.workforce.workforce_models import AgentSpec
from waspid.sdk import Event, ConversationExecutionStatus
from waspid.sdk.event import ConversationStateUpdateEvent

_logger = logging.getLogger(__name__)

_SUCCESS_TERMINAL = {ConversationExecutionStatus.FINISHED}


def _admin_state() -> InjectorState:
    state = InjectorState()
    setattr(state, USER_CONTEXT_ATTR, ADMIN)
    return state


async def _read_last_agent_message(state: InjectorState, conversation_id: UUID) -> str | None:
    """Walk the conversation's events and return the last agent message text."""
    from waspid.app_server.config import get_event_service

    last_text: str | None = None
    async with get_event_service(state) as event_service:
        page_id: str | None = None
        while True:
            page = await event_service.search_events(
                conversation_id,
                kind__eq='MessageEvent',
                page_id=page_id,
                limit=100,
            )
            for event in page.items:
                if getattr(event, 'source', None) != 'agent':
                    continue
                message = getattr(event, 'llm_message', None)
                content = getattr(message, 'content', None) or []
                texts = [
                    getattr(part, 'text', '')
                    for part in content
                    if getattr(part, 'text', None)
                ]
                if texts:
                    last_text = '\n'.join(texts)
            page_id = getattr(page, 'next_page_id', None)
            if not page_id:
                break
    return last_text


class WorkflowHandoffProcessor(EventCallbackProcessor):
    """Advances a workflow run when an agent conversation terminates."""

    run_id: UUID

    async def __call__(
        self,
        conversation_id: UUID,
        callback: EventCallback,
        event: Event,
    ) -> EventCallbackResult | None:
        if not isinstance(event, ConversationStateUpdateEvent):
            return None
        if event.key != 'execution_status':
            return None
        try:
            exec_status = ConversationExecutionStatus(event.value)
        except ValueError:
            return None
        if not exec_status.is_terminal():
            return None

        from waspid.app_server.config import get_db_session
        from waspid.app_server.workforce.workflow_run_service import (
            WorkflowRunStore,
            WorkflowRuntime,
        )

        state = _admin_state()
        success = exec_status in _SUCCESS_TERMINAL
        error = None if success else f'terminal status: {exec_status.value}'

        async with get_db_session(state) as db_session:
            runtime = WorkflowRuntime(
                store=WorkflowRunStore(db_session=db_session),
                gateway=LiveAgentGateway(),
                action_executor=LiveActionExecutor(),
            )
            try:
                await runtime.handle_agent_finished(
                    conversation_id, success=success, error=error
                )
            except Exception:
                _logger.exception(
                    'Workflow handoff failed for conversation %s', conversation_id
                )
                return EventCallbackResult(
                    status=EventCallbackResultStatus.ERROR,
                    event_callback_id=callback.id,
                    event_id=event.id,
                    conversation_id=conversation_id,
                )

        # Terminal status reached: this callback's job is done.
        callback.status = EventCallbackStatus.COMPLETED
        return EventCallbackResult(
            status=EventCallbackResultStatus.SUCCESS,
            event_callback_id=callback.id,
            event_id=event.id,
            conversation_id=conversation_id,
        )


@dataclass
class LiveAgentGateway:
    """Launches workforce agents as real app conversations."""

    async def launch_agent(
        self,
        run: WorkflowRun,
        task: WorkflowTask,
        agent: AgentSpec,
        instructions: str,
        kickoff: str,
    ) -> UUID:
        from waspid.agent_server.models import SendMessageRequest, TextContent
        from waspid.app_server.app_conversation.app_conversation_models import (
            AppConversationStartRequest,
            ConversationTrigger,
        )
        from waspid.app_server.config import get_app_conversation_service

        conversation_id = uuid4()
        request = AppConversationStartRequest(
            conversation_id=conversation_id,
            initial_message=SendMessageRequest(
                role='user',
                content=[TextContent(text=kickoff)],
                run=True,
            ),
            system_message_suffix=instructions,
            title=f'{run.name} — {agent.name}',
            trigger=ConversationTrigger.AUTOMATION,
            processors=[WorkflowHandoffProcessor(run_id=run.id)],
        )

        state = InjectorState()
        setattr(
            state,
            USER_CONTEXT_ATTR,
            _user_context_for(run.user_id),
        )

        async def drive_start() -> None:
            try:
                async with get_app_conversation_service(state) as service:
                    async for _start_task in service.start_app_conversation(request):
                        pass  # drive the start process to completion
            except Exception:
                _logger.exception(
                    'Agent launch failed for workflow %s agent %s',
                    run.id,
                    agent.name,
                )

        # The start process (sandbox boot etc.) is slow; drive it in the
        # background. The conversation id is pre-assigned so the runtime
        # can track it immediately; stalled launches are caught by the
        # task timeout.
        asyncio.create_task(drive_start())
        return conversation_id

    async def read_output(self, conversation_id: UUID) -> str | None:
        return await _read_last_agent_message(_admin_state(), conversation_id)


def _user_context_for(user_id: str | None):
    from waspid.app_server.user.specifiy_user_context import SpecifyUserContext

    return SpecifyUserContext(user_id=user_id)


@dataclass
class LiveActionExecutor:
    """Runs workflow edge actions through the Integration Hub."""

    async def execute_action(
        self,
        run: WorkflowRun,
        agent_name: str,
        provider: str,
        tool: str,
        params: dict[str, str],
    ) -> tuple[bool, str | None]:
        from waspid.app_server.config import get_db_session, get_httpx_client
        from waspid.app_server.integrations_hub.hub_service import (
            IntegrationHubService,
        )

        state = _admin_state()
        async with (
            get_db_session(state) as db_session,
            get_httpx_client(state) as httpx_client,
        ):
            service = IntegrationHubService(
                db_session=db_session, user_id=run.user_id
            )
            result = await service.execute(
                httpx_client,
                provider,
                tool,
                params,
                run_id=run.id,
                agent_name=agent_name,
            )
            return result.ok, result.error
