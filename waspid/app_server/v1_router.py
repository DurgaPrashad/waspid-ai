from fastapi import APIRouter

from waspid.app_server.app_conversation import app_conversation_router
from waspid.app_server.config_api.config_router import router as config_router
from waspid.app_server.event import event_router
from waspid.app_server.event_callback import (
    webhook_router,
)
from waspid.app_server.git.git_router import router as git_router
from waspid.app_server.pending_messages.pending_message_router import (
    router as pending_message_router,
)
from waspid.app_server.sandbox import sandbox_router, sandbox_spec_router
from waspid.app_server.secrets.secrets_router import (
    router as secrets_router,
)
from waspid.app_server.settings.settings_router import (
    router as settings_router,
)
from waspid.app_server.user import skills_router, user_router
from waspid.app_server.web_client import web_client_router
from waspid.app_server.integrations_hub.hub_router import (
    router as integrations_hub_router,
)
from waspid.app_server.workforce.workforce_router import (
    router as workforce_router,
)

# Include routers
router = APIRouter(prefix='/api/v1')
router.include_router(event_router.router)
router.include_router(app_conversation_router.router)
router.include_router(pending_message_router)
router.include_router(sandbox_router.router)
router.include_router(sandbox_spec_router.router)
router.include_router(settings_router)
router.include_router(secrets_router)
router.include_router(user_router.router)
router.include_router(skills_router.router)
router.include_router(webhook_router.router)
router.include_router(web_client_router.router)
router.include_router(git_router)
router.include_router(config_router)
router.include_router(workforce_router)
router.include_router(integrations_hub_router)
