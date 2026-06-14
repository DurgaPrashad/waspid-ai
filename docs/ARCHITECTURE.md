<!-- Waspid AI OS -->
# Waspid Architecture

Waspid is an enterprise AI workforce operating system: a control plane
for creating, running, observing, and scaling AI agents. It is built on
an MIT-licensed open-source agent SDK as its agent runtime (full
attribution in [CREDITS.md](../CREDITS.md)).

## High-level layout

```
┌─────────────────────────────────────────────────────────┐
│ frontend/            React 19 + React Router 7 SPA      │
│   workforce surfaces: /agents /workflows /monitoring     │
│   conversation UI, settings, org management              │
├─────────────────────────────────────────────────────────┤
│ waspid/app_server  FastAPI control plane (/api/v1)    │
│   conversations · sandboxes · settings · secrets · git   │
│   events · webhooks · MCP · users                        │
├─────────────────────────────────────────────────────────┤
│ Agent runtime         waspid-sdk / agent-server        │
│   one sandbox per conversation (Docker, local, remote)   │
├─────────────────────────────────────────────────────────┤
│ enterprise/           multi-tenant SaaS layer (optional) │
│   Keycloak SSO · orgs/RBAC · Stripe billing · audit      │
│   integrations: GitHub GitLab Jira Linear Slack …        │
└─────────────────────────────────────────────────────────┘
```

## Control plane (`waspid/app_server`)

- **app_conversation/** — the core resource. A conversation is one agent
  run: lifecycle, events, routing to the right runtime (native SDK agent
  or ACP providers such as Claude Code / Codex / Gemini CLI).
- **sandbox/** — pluggable sandbox services: `docker_sandbox_service`
  (default), `process_sandbox_service` (local), `remote_sandbox_service`
  (multi-node / Kubernetes-ready). Sandboxes authenticate back to the
  control plane with per-session API keys.
- **settings/ & secrets/** — per-user LLM provider config and secret
  storage; secrets flow control-plane → sandbox, never through clients.
- **event/ & event_callback/** — event persistence (filesystem, S3, GCS)
  and webhook fan-out.
- **integrations/** — git providers: GitHub, GitLab, Bitbucket (+ Data
  Center), Azure DevOps, Forgejo.
- **integrations_hub/** — the universal connector layer: per-user
  credentialed connections, the provider/tool registry, server-side
  tool executors (Slack, GitHub, HubSpot, Discord, generic webhook),
  health checks, and the tool-call log. Workflow edge actions execute
  through it. See [INTEGRATIONS_GUIDE.md](INTEGRATIONS_GUIDE.md).
- Dependency injection via `config.py` injectors makes each service
  swappable per deployment (the enterprise server overrides them).

## Provider abstraction

LLM access goes through LiteLLM. A provider + API key is sufficient —
OpenAI, Anthropic, Google Gemini, Grok, OpenRouter, DeepSeek, Ollama,
Azure OpenAI, and AWS Bedrock are configurable from the Settings UI or
`waspid provider add` with no code changes. Model verification lists
live in `frontend/src/utils/verified-models.ts`.

## Workforce surfaces (frontend)

- **/agents** — the active fleet, composed from real conversation data.
- **/workforce** — the Workforce Builder (agent factory): describe an
  objective, the Architect generates the workforce, blueprints are
  saved/cloned/exported, and agents launch as real runs. See
  [AGENT_FACTORY.md](AGENT_FACTORY.md).
- **/monitoring** — every run with lifecycle, model, cost, last activity.
- **/workflows** — the execution dashboard for the workflow runtime:
  live run status, per-agent tasks, approvals, event timeline, final
  deliverable. The runtime itself lives in
  `waspid/app_server/workforce/workflow_run_service.py`, with
  webhook-driven hand-offs via
  `workflow_live.WorkflowHandoffProcessor`. See
  [WORKFLOWS_GUIDE.md](WORKFLOWS_GUIDE.md).

## Enterprise layer (`enterprise/`)

A separate FastAPI server (`saas_server.py`) that extends the control
plane with Keycloak auth, multi-tenant organizations, RBAC, Stripe
billing, audit/analytics (PostHog + custom telemetry), and chat-ops
integrations (Slack, Jira, Linear). PostgreSQL + Alembic. Licensed under
Polyform Free Trial (see `enterprise/LICENSE`).

## Naming note

The Python package directory is `waspid/` and on-disk state lives in
`~/.waspid`. This is intentional: Waspid pins the upstream SDK
packages (`waspid-sdk`, `waspid-agent-server`, `waspid-tools`,
`waspid-aci`) and keeps wire/protocol compatibility with them. All
user-facing branding is Waspid.

## Roadmap (not yet implemented)

These are designed-for but **not** present in the codebase today:

- Voice AI infrastructure (telephony, STT/TTS providers, call center
  dashboard).
- Hosted blueprint marketplace (sharing is file-based export/import
  today) and architect feedback loops driven by run outcomes.
- Workflow loops/iteration (cyclic edges are broken at deploy time),
  supervisor-driven rerouting, websocket push for the dashboard
  (currently polling), and sandbox kill on cancel.
- Integration Hub: browser-redirect OAuth flows (pasted tokens work),
  per-agent tool allow/deny lists, and automatic write-through of Hub
  credentials into sandbox secrets.
