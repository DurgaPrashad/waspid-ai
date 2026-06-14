# Waspid AI OS
"""Server-side tool executors: real REST calls per provider.

Every executor takes an ``httpx.AsyncClient`` so tests can inject a
``MockTransport``. Executors raise nothing — failures are returned as
``ToolCallResult(ok=False, …)`` so callers (workflow actions, the
execute API) decide how to react.
"""

from __future__ import annotations

import json
from typing import Awaitable, Callable

import httpx

from waspid.app_server.integrations_hub.hub_models import (
    INTEGRATION_REGISTRY,
    ToolCallResult,
    ToolExecution,
)

Executor = Callable[
    [httpx.AsyncClient, str, str | None, dict[str, str]],
    Awaitable[ToolCallResult],
]


def _result(response: httpx.Response) -> ToolCallResult:
    try:
        data = response.json()
    except ValueError:
        data = response.text[:2000]
    ok = response.is_success
    # Slack returns 200 with {"ok": false} on errors.
    if ok and isinstance(data, dict) and data.get('ok') is False:
        ok = False
    return ToolCallResult(
        ok=ok,
        status_code=response.status_code,
        data=data,
        error=None if ok else f'HTTP {response.status_code}: {str(data)[:300]}',
    )


async def _guard(call: Awaitable[httpx.Response]) -> ToolCallResult:
    try:
        return _result(await call)
    except httpx.HTTPError as exc:
        return ToolCallResult(ok=False, error=f'request failed: {exc}')


def _refuse_unsafe_url(url: str) -> ToolCallResult | None:
    """SSRF defense in depth for user-supplied target URLs.

    Validated at connection creation too, but DNS can change between
    save and use, so re-check before every call.
    """
    from waspid.app_server.integrations_hub.url_guard import (
        UnsafeUrlError,
        validate_outbound_url,
    )

    try:
        validate_outbound_url(url)
    except UnsafeUrlError as exc:
        return ToolCallResult(ok=False, error=f'unsafe webhook URL: {exc}')
    return None


# --- Slack -----------------------------------------------------------------


async def slack_send_message(client, credential, base_url, params):
    return await _guard(
        client.post(
            'https://slack.com/api/chat.postMessage',
            headers={'Authorization': f'Bearer {credential}'},
            json={'channel': params['channel'], 'text': params['text']},
        )
    )


async def slack_list_channels(client, credential, base_url, params):
    return await _guard(
        client.get(
            'https://slack.com/api/conversations.list',
            headers={'Authorization': f'Bearer {credential}'},
            params={'types': 'public_channel', 'limit': 200},
        )
    )


# --- Discord (channel webhook) ----------------------------------------------


async def discord_send_message(client, credential, base_url, params):
    error = _refuse_unsafe_url(credential)
    if error:
        return error
    return await _guard(client.post(credential, json={'content': params['text']}))


# --- GitHub ------------------------------------------------------------------


def _github_headers(credential: str) -> dict:
    return {
        'Authorization': f'Bearer {credential}',
        'Accept': 'application/vnd.github+json',
    }


async def github_create_issue(client, credential, base_url, params):
    return await _guard(
        client.post(
            f'https://api.github.com/repos/{params["repo"]}/issues',
            headers=_github_headers(credential),
            json={'title': params['title'], 'body': params.get('body', '')},
        )
    )


async def github_create_pull_request(client, credential, base_url, params):
    return await _guard(
        client.post(
            f'https://api.github.com/repos/{params["repo"]}/pulls',
            headers=_github_headers(credential),
            json={
                'title': params['title'],
                'head': params['head'],
                'base': params['base'],
                'body': params.get('body', ''),
            },
        )
    )


async def github_add_comment(client, credential, base_url, params):
    return await _guard(
        client.post(
            f'https://api.github.com/repos/{params["repo"]}/issues/'
            f'{params["number"]}/comments',
            headers=_github_headers(credential),
            json={'body': params['body']},
        )
    )


# --- HubSpot -----------------------------------------------------------------

_HUBSPOT = 'https://api.hubapi.com'


def _hubspot_headers(credential: str) -> dict:
    return {'Authorization': f'Bearer {credential}'}


async def hubspot_create_contact(client, credential, base_url, params):
    properties = {
        key: params[key]
        for key in ('email', 'firstname', 'lastname', 'company')
        if params.get(key)
    }
    return await _guard(
        client.post(
            f'{_HUBSPOT}/crm/v3/objects/contacts',
            headers=_hubspot_headers(credential),
            json={'properties': properties},
        )
    )


async def hubspot_update_contact(client, credential, base_url, params):
    try:
        properties = json.loads(params['properties_json'])
    except (ValueError, KeyError) as exc:
        return ToolCallResult(ok=False, error=f'invalid properties_json: {exc}')
    return await _guard(
        client.patch(
            f'{_HUBSPOT}/crm/v3/objects/contacts/{params["contact_id"]}',
            headers=_hubspot_headers(credential),
            json={'properties': properties},
        )
    )


async def hubspot_search_contacts(client, credential, base_url, params):
    return await _guard(
        client.post(
            f'{_HUBSPOT}/crm/v3/objects/contacts/search',
            headers=_hubspot_headers(credential),
            json={'query': params['query'], 'limit': 20},
        )
    )


async def hubspot_create_note(client, credential, base_url, params):
    return await _guard(
        client.post(
            f'{_HUBSPOT}/crm/v3/objects/notes',
            headers=_hubspot_headers(credential),
            json={
                'properties': {'hs_note_body': params['body']},
                'associations': [
                    {
                        'to': {'id': params['contact_id']},
                        'types': [
                            {
                                'associationCategory': 'HUBSPOT_DEFINED',
                                'associationTypeId': 202,
                            }
                        ],
                    }
                ],
            },
        )
    )


# --- Generic webhook ----------------------------------------------------------


async def webhook_post(client, credential, base_url, params):
    error = _refuse_unsafe_url(credential)
    if error:
        return error
    try:
        payload = json.loads(params['payload_json'])
    except (ValueError, KeyError) as exc:
        return ToolCallResult(ok=False, error=f'invalid payload_json: {exc}')
    return await _guard(client.post(credential, json=payload))


# --- Health checks --------------------------------------------------------------


async def check_slack(client, credential, base_url):
    return await _guard(
        client.post(
            'https://slack.com/api/auth.test',
            headers={'Authorization': f'Bearer {credential}'},
        )
    )


async def check_github(client, credential, base_url):
    return await _guard(
        client.get('https://api.github.com/user', headers=_github_headers(credential))
    )


async def check_hubspot(client, credential, base_url):
    return await _guard(
        client.get(
            f'{_HUBSPOT}/crm/v3/objects/contacts?limit=1',
            headers=_hubspot_headers(credential),
        )
    )


EXECUTORS: dict[tuple[str, str], Executor] = {
    ('slack', 'send_message'): slack_send_message,
    ('slack', 'list_channels'): slack_list_channels,
    ('discord', 'send_message'): discord_send_message,
    ('github', 'create_issue'): github_create_issue,
    ('github', 'create_pull_request'): github_create_pull_request,
    ('github', 'add_comment'): github_add_comment,
    ('hubspot', 'create_contact'): hubspot_create_contact,
    ('hubspot', 'update_contact'): hubspot_update_contact,
    ('hubspot', 'search_contacts'): hubspot_search_contacts,
    ('hubspot', 'create_note'): hubspot_create_note,
    ('webhook', 'post'): webhook_post,
}

HEALTH_CHECKS = {
    'slack': check_slack,
    'github': check_github,
    'hubspot': check_hubspot,
}


async def execute_tool(
    client: httpx.AsyncClient,
    provider: str,
    tool: str,
    credential: str,
    base_url: str | None,
    params: dict[str, str],
) -> ToolCallResult:
    """Validate against the registry and run the matching executor."""
    spec = INTEGRATION_REGISTRY.get(provider)
    if spec is None:
        return ToolCallResult(ok=False, error=f'unknown provider: {provider}')
    tool_spec = next((t for t in spec.tools if t.name == tool), None)
    if tool_spec is None:
        return ToolCallResult(ok=False, error=f'unknown tool: {provider}.{tool}')
    if tool_spec.execution != ToolExecution.SERVER:
        return ToolCallResult(
            ok=False,
            error=(
                f'{provider}.{tool} executes via {tool_spec.execution.value}, '
                'not server-side'
            ),
        )
    missing = [p for p in tool_spec.required_params if not params.get(p)]
    if missing:
        return ToolCallResult(ok=False, error=f'missing params: {", ".join(missing)}')
    executor = EXECUTORS[(provider, tool)]
    return await executor(client, credential, base_url, params)
