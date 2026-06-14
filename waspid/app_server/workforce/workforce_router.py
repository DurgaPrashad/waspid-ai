# Waspid AI OS
"""Workforce router: agent factory and blueprint endpoints under /api/v1."""

import logging
import warnings
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from waspid.app_server.config import depends_db_session
from waspid.app_server.settings.settings_models import Settings
from waspid.app_server.user_auth import get_user_id, get_user_settings
from waspid.app_server.workforce.architect_service import (
    ArchitectError,
    ArchitectService,
)
from waspid.app_server.workforce.workforce_blueprint_service import (
    WorkforceBlueprintService,
)
from waspid.app_server.workforce.workflow_live import (
    LiveActionExecutor,
    LiveAgentGateway,
)
from waspid.app_server.workforce.workflow_models import (
    StartWorkflowRunRequest,
    WorkflowRun,
    WorkflowRunDetail,
    WorkflowRunPage,
    WorkflowTask,
)
from waspid.app_server.workforce.workflow_run_service import (
    WorkflowRunStore,
    WorkflowRuntime,
)
from waspid.app_server.workforce.workforce_models import (
    BLUEPRINT_EXPORT_VERSION,
    BlueprintExport,
    CreateBlueprintRequest,
    GenerateWorkforceRequest,
    WorkforceBlueprint,
    WorkforceBlueprintPage,
    WorkforceDefinition,
    WorkforceRequirements,
    required_integration_providers,
)

from waspid.app_server.utils.user_rate_limit import UserRateLimiter

_logger = logging.getLogger(__name__)
_audit_logger = logging.getLogger('waspid.audit')

router = APIRouter(prefix='/workforce', tags=['Workforce'])
db_session_dependency = depends_db_session()

# Each generation is an LLM call billed to the user: cap the rate.
_generate_rate_limit = UserRateLimiter(max_requests=10, window_seconds=60)


def _blueprint_service(
    db_session: Annotated[AsyncSession, db_session_dependency],
    user_id: Annotated[str | None, Depends(get_user_id)],
) -> WorkforceBlueprintService:
    return WorkforceBlueprintService(db_session=db_session, user_id=user_id)


def _architect_from_settings(settings: Settings | None) -> ArchitectService:
    """Build an architect bound to the user's configured LLM."""
    llm = settings.agent_settings.llm if settings else None
    if llm is None or not llm.model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                'No LLM is configured. Set a provider and model under '
                'Settings → LLM before generating a workforce.'
            ),
        )
    model = llm.model
    base_url = llm.base_url
    api_key = None
    if llm.api_key is not None:
        get_secret = getattr(llm.api_key, 'get_secret_value', None)
        api_key = get_secret() if get_secret else str(llm.api_key)

    def complete(messages: list[dict]) -> str:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            import litellm

        response = litellm.completion(
            model=model,
            messages=messages,
            api_key=api_key,
            base_url=base_url,
            temperature=0.2,
        )
        content = response.choices[0].message.content  # type: ignore[union-attr]
        if not content:
            raise ArchitectError('LLM returned an empty response')
        return content

    return ArchitectService(complete=complete)


@router.post('/generate')
async def generate_workforce(
    request: GenerateWorkforceRequest,
    settings: Annotated[Settings | None, Depends(get_user_settings)],
    user_id: Annotated[str | None, Depends(get_user_id)],
) -> WorkforceDefinition:
    """Generate a workforce definition from a natural-language objective."""
    if not _generate_rate_limit.allow(user_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail='Workforce generation rate limit reached; retry shortly.',
        )
    architect = _architect_from_settings(settings)
    try:
        return await architect.generate(request.objective, request.max_agents)
    except ArchitectError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f'Workforce generation failed: {exc}',
        )


@router.post('/blueprints', status_code=status.HTTP_201_CREATED)
async def create_blueprint(
    request: CreateBlueprintRequest,
    service: Annotated[WorkforceBlueprintService, Depends(_blueprint_service)],
) -> WorkforceBlueprint:
    return await service.create(request.name, request.definition)


@router.get('/blueprints')
async def list_blueprints(
    service: Annotated[WorkforceBlueprintService, Depends(_blueprint_service)],
) -> WorkforceBlueprintPage:
    return WorkforceBlueprintPage(items=await service.list())


@router.get('/blueprints/{blueprint_id}')
async def get_blueprint(
    blueprint_id: UUID,
    service: Annotated[WorkforceBlueprintService, Depends(_blueprint_service)],
) -> WorkforceBlueprint:
    blueprint = await service.get(blueprint_id)
    if blueprint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return blueprint


@router.delete('/blueprints/{blueprint_id}')
async def delete_blueprint(
    blueprint_id: UUID,
    service: Annotated[WorkforceBlueprintService, Depends(_blueprint_service)],
) -> dict:
    if not await service.delete(blueprint_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {'success': True}


@router.post('/blueprints/{blueprint_id}/clone', status_code=status.HTTP_201_CREATED)
async def clone_blueprint(
    blueprint_id: UUID,
    service: Annotated[WorkforceBlueprintService, Depends(_blueprint_service)],
) -> WorkforceBlueprint:
    blueprint = await service.clone(blueprint_id)
    if blueprint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return blueprint


@router.get('/blueprints/{blueprint_id}/export')
async def export_blueprint(
    blueprint_id: UUID,
    service: Annotated[WorkforceBlueprintService, Depends(_blueprint_service)],
) -> BlueprintExport:
    blueprint = await service.get(blueprint_id)
    if blueprint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return BlueprintExport(name=blueprint.name, definition=blueprint.definition)


@router.post('/blueprints/import', status_code=status.HTTP_201_CREATED)
async def import_blueprint(
    request: BlueprintExport,
    service: Annotated[WorkforceBlueprintService, Depends(_blueprint_service)],
) -> WorkforceBlueprint:
    if request.version > BLUEPRINT_EXPORT_VERSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f'Blueprint export version {request.version} is newer than '
                f'this server supports ({BLUEPRINT_EXPORT_VERSION}).'
            ),
        )
    return await service.create(request.name, request.definition)


# ---------------------------------------------------------------------------
# Workflow runs (the autonomous execution layer)
# ---------------------------------------------------------------------------


def _runtime(
    db_session: Annotated[AsyncSession, db_session_dependency],
    user_id: Annotated[str | None, Depends(get_user_id)],
) -> WorkflowRuntime:
    return WorkflowRuntime(
        store=WorkflowRunStore(db_session=db_session, user_id=user_id),
        gateway=LiveAgentGateway(),
        action_executor=LiveActionExecutor(),
    )


async def _check_requirements(
    definition: WorkforceDefinition,
    settings: Settings | None,
    db_session: AsyncSession,
    user_id: str | None,
) -> WorkforceRequirements:
    from waspid.app_server.integrations_hub.hub_models import (
        INTEGRATION_REGISTRY,
    )
    from waspid.app_server.integrations_hub.hub_service import (
        IntegrationHubService,
    )

    llm = settings.agent_settings.llm if settings else None
    required = required_integration_providers(
        definition, set(INTEGRATION_REGISTRY)
    )
    hub = IntegrationHubService(db_session=db_session, user_id=user_id)
    connected = {c.provider for c in await hub.list_connections()}
    return WorkforceRequirements(
        llm_configured=bool(llm and llm.model),
        required_integrations=required,
        missing_integrations=[p for p in required if p not in connected],
    )


@router.post('/runs', status_code=status.HTTP_201_CREATED)
async def start_workflow_run(
    request: StartWorkflowRunRequest,
    runtime: Annotated[WorkflowRuntime, Depends(_runtime)],
    blueprints: Annotated[WorkforceBlueprintService, Depends(_blueprint_service)],
    user_id: Annotated[str | None, Depends(get_user_id)],
    settings: Annotated[Settings | None, Depends(get_user_settings)],
    db_session: Annotated[AsyncSession, db_session_dependency],
) -> WorkflowRun:
    """Deploy a workforce: create a run and start its entry agents.

    Requirements (configured LLM, connected integrations referenced by
    the definition) are checked first; missing ones return 409 with a
    structured payload unless ``ignore_missing_requirements`` is set.
    """
    definition = request.definition
    blueprint_id = request.blueprint_id
    name = request.name
    if definition is None:
        if blueprint_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Provide a definition or a blueprint_id.',
            )
        blueprint = await blueprints.get(blueprint_id)
        if blueprint is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        definition = blueprint.definition
        name = name or blueprint.name

    requirements = await _check_requirements(
        definition, settings, db_session, user_id
    )
    if not requirements.satisfied and not request.ignore_missing_requirements:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'message': 'Workforce requirements are not satisfied.',
                'llm_configured': requirements.llm_configured,
                'required_integrations': requirements.required_integrations,
                'missing_integrations': requirements.missing_integrations,
            },
        )

    run = await runtime.start_run(
        definition, name=name, user_id=user_id, blueprint_id=blueprint_id
    )
    _audit_logger.info(
        'workflow_run_started user=%s run=%s agents=%d',
        user_id,
        run.id,
        len(definition.agents),
    )
    return run


@router.get('/runs')
async def list_workflow_runs(
    runtime: Annotated[WorkflowRuntime, Depends(_runtime)],
) -> WorkflowRunPage:
    await runtime.check_timeouts()
    return WorkflowRunPage(items=await runtime.store.list_runs())


@router.get('/runs/{run_id}')
async def get_workflow_run(
    run_id: UUID,
    runtime: Annotated[WorkflowRuntime, Depends(_runtime)],
) -> WorkflowRunDetail:
    await runtime.check_timeouts()
    run = await runtime.store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return WorkflowRunDetail(
        run=run,
        tasks=await runtime.store.get_tasks(run_id),
        events=await runtime.store.get_events(run_id),
    )


async def _run_action(
    runtime: WorkflowRuntime, run_id: UUID, action: str
) -> WorkflowRun:
    if await runtime.store.get_run(run_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    run = await getattr(runtime, action)(run_id)
    assert run is not None
    return run


@router.post('/runs/{run_id}/pause')
async def pause_workflow_run(
    run_id: UUID, runtime: Annotated[WorkflowRuntime, Depends(_runtime)]
) -> WorkflowRun:
    return await _run_action(runtime, run_id, 'pause')


@router.post('/runs/{run_id}/resume')
async def resume_workflow_run(
    run_id: UUID, runtime: Annotated[WorkflowRuntime, Depends(_runtime)]
) -> WorkflowRun:
    return await _run_action(runtime, run_id, 'resume')


@router.post('/runs/{run_id}/cancel')
async def cancel_workflow_run(
    run_id: UUID, runtime: Annotated[WorkflowRuntime, Depends(_runtime)]
) -> WorkflowRun:
    return await _run_action(runtime, run_id, 'cancel')


@router.post('/runs/{run_id}/tasks/{task_id}/approve')
async def approve_workflow_task(
    run_id: UUID,
    task_id: UUID,
    runtime: Annotated[WorkflowRuntime, Depends(_runtime)],
) -> WorkflowTask:
    if await runtime.store.get_run(run_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    task = await runtime.approve_task(run_id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return task


@router.post('/runs/{run_id}/tasks/{task_id}/retry')
async def retry_workflow_task(
    run_id: UUID,
    task_id: UUID,
    runtime: Annotated[WorkflowRuntime, Depends(_runtime)],
) -> WorkflowTask:
    if await runtime.store.get_run(run_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    task = await runtime.retry_task(run_id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return task
