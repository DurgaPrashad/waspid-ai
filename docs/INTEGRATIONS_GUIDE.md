# Waspid Integrations Guide

## Integration Hub

The Integration Hub (bottom of the **Integrations** page, API under
`/api/v1/integrations-hub`) is the universal connector layer: one
interface for every external system, with a per-provider tool registry.

### Connecting a provider

Each provider takes a credential — an API key, a webhook URL, or a
pasted OAuth access token — plus a base URL where required (Jira,
Salesforce). Credentials are encrypted at rest. One connection per
provider per user; the Hub shows connection health (live checks are
implemented for Slack, GitHub, and HubSpot).

### How tools execute

Every tool in the registry declares its execution path honestly:

| Path | Meaning |
| --- | --- |
| **Runs on Waspid** | The server executes the REST call directly. Used by workflow actions and `POST /integrations-hub/tools/{provider}/{tool}/execute`. |
| **Runs in agent sandbox** | Add the credential as a custom secret (the provider card names the env var, e.g. `HUBSPOT_TOKEN`) and agents call the provider's API themselves. |
| **Via MCP server** | Connect the provider's MCP server under *Settings → MCP* (e.g. Notion, Linear, Google). |

Server-executed tools today: Slack (`send_message`, `list_channels`),
Discord (`send_message` via webhook), GitHub (`create_issue`,
`create_pull_request`, `add_comment`), HubSpot (`create_contact`,
`update_contact`, `search_contacts`, `create_note`), and a generic
`webhook.post` for anything that accepts inbound webhooks.

### Workflow actions

Workflow edges can carry integration actions that fire automatically
when the handoff triggers:

```json
{
  "from_agent": "Lead Qualification Agent",
  "to_agent": "CRM Agent",
  "actions": [
    {
      "provider": "slack",
      "tool": "send_message",
      "params": { "channel": "#sales", "text": "Qualified: {{output}}" }
    }
  ]
}
```

`{{output}}` is the upstream agent's final output, `{{objective}}` the
run objective, and `{{Agent Name}}` any completed agent's output from
shared memory. Action failures are logged as run events
(`action_failed`) but do not fail the run.

### Observability

Every tool call — from workflows or the API — is logged with provider,
tool, status, latency, and the originating run/agent. The Hub shows
totals, failure counts, average latency, and the recent call log
(`GET /integrations-hub/tool-calls`).

### Not yet built (honest status)

The browser-redirect OAuth flow (providers marked `oauth_token` accept
pasted tokens); per-agent tool allow/deny lists; automatic write-through
of Hub credentials into sandbox secrets (add the custom secret manually
for sandbox-path tools).

## Git providers (core)

Waspid connects to git hosting providers so agents can clone, branch,
and open pull requests on your behalf. Supported in the core control
plane (`waspid/app_server/integrations/`):

- GitHub
- GitLab
- Bitbucket and Bitbucket Data Center
- Azure DevOps
- Forgejo

Connect a provider under *Settings → Integrations* (token-based via the
V1 secrets endpoints on self-hosted deployments; OAuth on enterprise
deployments).

### Repository conventions

- `.waspid/microagents/` — repository knowledge for agents
  (see [AGENTS_GUIDE.md](AGENTS_GUIDE.md)).
- `.waspid/setup.sh` — runs at conversation start.
- On GitLab/Azure DevOps, an `waspid-config` repository can hold
  org-level configuration; on other providers a `.waspid` repository
  serves the same purpose.

## Enterprise integrations (`enterprise/integrations/`)

The enterprise layer adds chat-ops and project-management connectors:

| Integration | Capabilities |
| --- | --- |
| Slack | Start and follow agent runs from Slack |
| Jira / Jira Data Center | Issue-driven agent runs, status sync |
| Linear | Issue-driven agent runs |
| GitHub / GitLab apps | Webhooks, PR automation, app installations |

Each follows a consistent pattern — service class, storage models, API
endpoints — which is also the template for building new connectors.

## MCP servers

Waspid speaks the Model Context Protocol. Add MCP servers under
*Settings → MCP* (SSE, stdio, and streamable-HTTP transports) to give
agents additional tools — internal APIs, databases, SaaS products —
without modifying Waspid.

## Webhooks / event callbacks

Subscribe external systems to conversation events via the
event-callback endpoints (see [API.md](API.md)) to build custom
routing, notifications, or audit pipelines.
