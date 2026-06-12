# Waspid API

The Waspid control plane is a FastAPI application. All functionality in
the web UI is backed by the same REST + WebSocket API.

## Interactive documentation

With the server running, the complete, always-current API reference is
served by the backend itself:

- Swagger UI: `http://localhost:3000/docs`
- OpenAPI JSON: `http://localhost:3000/openapi.json`

## Surface overview

All v1 endpoints are mounted under `/api/v1` (see
`waspid/app_server/v1_router.py`). The main resource groups:

| Group | Purpose |
| --- | --- |
| `app-conversations` | Create and manage agent runs (conversations), events, status |
| `sandboxes` | Sandbox lifecycle, sandbox-scoped secrets |
| `settings` | User settings: LLM provider/model, agent options |
| `secrets` | Custom secrets and git-provider tokens |
| `users` | Current-user info |
| `mcp` | MCP server configuration (also mounted at `/mcp`) |
| `event-callbacks` / webhooks | Event subscriptions for external systems |
| `git` | Repository listing/search across connected providers |

A health check is exposed at `/health`.

## Authentication

- **Local / self-hosted:** session-based; conversation-scoped calls use
  the `X-Session-API-Key` header issued per sandbox.
- **Enterprise (SaaS):** bearer tokens via Keycloak; per-user API keys
  can be created under *Settings → API Keys*.

## Realtime events

Agent events stream over a WebSocket per conversation; the frontend's
implementation in `frontend/src/` is the reference client.
