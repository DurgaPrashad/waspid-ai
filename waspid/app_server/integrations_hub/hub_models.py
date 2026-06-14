# Waspid AI OS
"""Models and the provider/tool registry for the Integration Hub."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, SecretStr


class CredentialKind(str, Enum):
    API_KEY = 'api_key'
    WEBHOOK_URL = 'webhook_url'
    # OAuth needs per-deployment app credentials; connections of this
    # kind can be stored (token paste) but Waspid does not yet run the
    # authorization-code flow itself.
    OAUTH_TOKEN = 'oauth_token'


class ToolExecution(str, Enum):
    SERVER = 'server'  # Waspid executes the call (workflow actions, API)
    SANDBOX = 'sandbox'  # agent uses the credential inside its sandbox
    MCP = 'mcp'  # use the provider's MCP server (Settings -> MCP)


class ToolSpec(BaseModel):
    name: str
    description: str
    execution: ToolExecution
    # Parameter name -> human description. Server tools validate that
    # required params are present at execution time.
    params: dict[str, str] = Field(default_factory=dict)
    required_params: list[str] = Field(default_factory=list)


class IntegrationProviderSpec(BaseModel):
    id: str
    name: str
    category: str
    credential_kind: CredentialKind
    # Env var name agents see when the user also adds the credential as
    # a custom secret (sandbox execution path).
    sandbox_env_var: str | None = None
    base_url_required: bool = False
    tools: list[ToolSpec] = Field(default_factory=list)
    notes: str = ''


def _server(name: str, description: str, params: dict[str, str], required: list[str]) -> ToolSpec:
    return ToolSpec(
        name=name,
        description=description,
        execution=ToolExecution.SERVER,
        params=params,
        required_params=required,
    )


def _sandbox(name: str, description: str) -> ToolSpec:
    return ToolSpec(name=name, description=description, execution=ToolExecution.SANDBOX)


def _mcp(name: str, description: str) -> ToolSpec:
    return ToolSpec(name=name, description=description, execution=ToolExecution.MCP)


INTEGRATION_REGISTRY: dict[str, IntegrationProviderSpec] = {
    spec.id: spec
    for spec in [
        IntegrationProviderSpec(
            id='slack',
            name='Slack',
            category='communication',
            credential_kind=CredentialKind.API_KEY,
            sandbox_env_var='SLACK_BOT_TOKEN',
            tools=[
                _server(
                    'send_message',
                    'Post a message to a channel',
                    {'channel': 'Channel ID or name', 'text': 'Message text'},
                    ['channel', 'text'],
                ),
                _server(
                    'list_channels',
                    'List public channels in the workspace',
                    {},
                    [],
                ),
            ],
            notes='Use a bot token (xoxb-…) with chat:write and channels:read scopes.',
        ),
        IntegrationProviderSpec(
            id='discord',
            name='Discord',
            category='communication',
            credential_kind=CredentialKind.WEBHOOK_URL,
            tools=[
                _server(
                    'send_message',
                    'Post a message via a channel webhook',
                    {'text': 'Message text'},
                    ['text'],
                ),
            ],
            notes='Create a webhook on the target channel and paste its URL.',
        ),
        IntegrationProviderSpec(
            id='github',
            name='GitHub',
            category='development',
            credential_kind=CredentialKind.API_KEY,
            sandbox_env_var='GITHUB_TOKEN',
            tools=[
                _server(
                    'create_issue',
                    'Create an issue in a repository',
                    {
                        'repo': 'owner/name',
                        'title': 'Issue title',
                        'body': 'Issue body (markdown)',
                    },
                    ['repo', 'title'],
                ),
                _server(
                    'create_pull_request',
                    'Open a pull request',
                    {
                        'repo': 'owner/name',
                        'title': 'PR title',
                        'head': 'Source branch',
                        'base': 'Target branch',
                        'body': 'PR description',
                    },
                    ['repo', 'title', 'head', 'base'],
                ),
                _server(
                    'add_comment',
                    'Comment on an issue or pull request',
                    {'repo': 'owner/name', 'number': 'Issue/PR number', 'body': 'Comment'},
                    ['repo', 'number', 'body'],
                ),
                _sandbox('clone_and_review', 'Clone, build, review code in the sandbox'),
            ],
            notes='Also available as a first-class git provider under Settings → Integrations.',
        ),
        IntegrationProviderSpec(
            id='gitlab',
            name='GitLab',
            category='development',
            credential_kind=CredentialKind.API_KEY,
            sandbox_env_var='GITLAB_TOKEN',
            tools=[
                _sandbox('manage_merge_requests', 'Create and review merge requests'),
                _sandbox('manage_issues', 'Create and update issues'),
            ],
            notes='Also available as a first-class git provider under Settings → Integrations.',
        ),
        IntegrationProviderSpec(
            id='hubspot',
            name='HubSpot',
            category='crm',
            credential_kind=CredentialKind.API_KEY,
            sandbox_env_var='HUBSPOT_TOKEN',
            tools=[
                _server(
                    'create_contact',
                    'Create a CRM contact (lead)',
                    {
                        'email': 'Contact email',
                        'firstname': 'First name',
                        'lastname': 'Last name',
                        'company': 'Company name',
                    },
                    ['email'],
                ),
                _server(
                    'update_contact',
                    'Update properties on a contact',
                    {'contact_id': 'HubSpot contact id', 'properties_json': 'JSON object of properties'},
                    ['contact_id', 'properties_json'],
                ),
                _server(
                    'search_contacts',
                    'Search contacts by email or name',
                    {'query': 'Search query'},
                    ['query'],
                ),
                _server(
                    'create_note',
                    'Attach a note to a contact',
                    {'contact_id': 'HubSpot contact id', 'body': 'Note text'},
                    ['contact_id', 'body'],
                ),
            ],
            notes='Use a private app access token with crm.objects.contacts scopes.',
        ),
        IntegrationProviderSpec(
            id='salesforce',
            name='Salesforce',
            category='crm',
            credential_kind=CredentialKind.OAUTH_TOKEN,
            sandbox_env_var='SALESFORCE_TOKEN',
            base_url_required=True,
            tools=[
                _sandbox('manage_leads', 'Create/update leads via the REST API'),
                _sandbox('manage_opportunities', 'Move pipeline stages, create tasks'),
            ],
            notes='Paste an access token and your instance URL; OAuth flow not yet built in.',
        ),
        IntegrationProviderSpec(
            id='pipedrive',
            name='Pipedrive',
            category='crm',
            credential_kind=CredentialKind.API_KEY,
            sandbox_env_var='PIPEDRIVE_TOKEN',
            tools=[
                _sandbox('manage_deals', 'Create/update deals and pipeline stages'),
                _sandbox('manage_persons', 'Create/update persons and notes'),
            ],
        ),
        IntegrationProviderSpec(
            id='notion',
            name='Notion',
            category='documents',
            credential_kind=CredentialKind.API_KEY,
            sandbox_env_var='NOTION_TOKEN',
            tools=[
                _mcp('manage_pages', 'Read/create/update pages via the Notion MCP server'),
                _sandbox('api_access', 'Direct REST access from the sandbox'),
            ],
            notes='Notion publishes an official MCP server — add it under Settings → MCP.',
        ),
        IntegrationProviderSpec(
            id='google_workspace',
            name='Google Workspace (Gmail, Docs, Sheets)',
            category='documents',
            credential_kind=CredentialKind.OAUTH_TOKEN,
            sandbox_env_var='GOOGLE_OAUTH_TOKEN',
            tools=[
                _mcp('gmail', 'Send/read mail via a Gmail MCP server'),
                _mcp('docs_sheets', 'Read/write Docs and Sheets via MCP'),
                _sandbox('api_access', 'Direct API access with a pasted OAuth token'),
            ],
            notes='Google APIs require OAuth; use an MCP server or paste a token.',
        ),
        IntegrationProviderSpec(
            id='microsoft365',
            name='Microsoft 365 (Outlook, Teams)',
            category='communication',
            credential_kind=CredentialKind.OAUTH_TOKEN,
            sandbox_env_var='MSGRAPH_TOKEN',
            tools=[
                _sandbox('outlook_mail', 'Send/read mail via Microsoft Graph'),
                _sandbox('teams_messages', 'Post Teams messages via Microsoft Graph'),
            ],
            notes='Microsoft Graph requires OAuth; paste a token or use an MCP server.',
        ),
        IntegrationProviderSpec(
            id='jira',
            name='Jira',
            category='project_management',
            credential_kind=CredentialKind.API_KEY,
            sandbox_env_var='JIRA_TOKEN',
            base_url_required=True,
            tools=[
                _sandbox('manage_issues', 'Create/update/transition issues'),
            ],
            notes='Enterprise deployments also have the chat-ops Jira integration.',
        ),
        IntegrationProviderSpec(
            id='linear',
            name='Linear',
            category='project_management',
            credential_kind=CredentialKind.API_KEY,
            sandbox_env_var='LINEAR_API_KEY',
            tools=[
                _mcp('manage_issues', "Use Linear's official MCP server"),
                _sandbox('api_access', 'GraphQL API access from the sandbox'),
            ],
        ),
        IntegrationProviderSpec(
            id='webhook',
            name='Generic Webhook',
            category='automation',
            credential_kind=CredentialKind.WEBHOOK_URL,
            tools=[
                _server(
                    'post',
                    'POST a JSON payload to the configured URL',
                    {'payload_json': 'JSON body to send'},
                    ['payload_json'],
                ),
            ],
            notes='Connect any system that accepts inbound webhooks (Zapier, n8n, …).',
        ),
    ]
}


class IntegrationConnection(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str | None = None
    provider: str
    name: str = ''
    base_url: str | None = None
    created_at: datetime | None = None
    last_check_at: datetime | None = None
    last_check_ok: bool | None = None


class CreateConnectionRequest(BaseModel):
    provider: str
    credential: SecretStr
    name: str = ''
    base_url: str | None = None


class ProviderStatus(BaseModel):
    """Registry entry plus the caller's connection state."""

    spec: IntegrationProviderSpec
    connection: IntegrationConnection | None = None


class ToolCallResult(BaseModel):
    ok: bool
    status_code: int | None = None
    data: dict | list | str | None = None
    error: str | None = None


class ExecuteToolRequest(BaseModel):
    params: dict[str, str] = Field(default_factory=dict)


class ToolCallLogEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str | None = None
    provider: str
    tool: str
    ok: bool
    status_code: int | None = None
    error: str | None = None
    latency_ms: int | None = None
    run_id: UUID | None = None
    agent_name: str | None = None
    created_at: datetime | None = None


class ToolCallStats(BaseModel):
    total: int
    failures: int
    avg_latency_ms: float | None = None


class ToolCallLogPage(BaseModel):
    items: list[ToolCallLogEntry]
    stats: ToolCallStats
