# Self-hosting Waspid

This guide covers running Waspid on your own infrastructure.

## One-command Docker Compose

```bash
git clone https://github.com/DurgaPrashad/waspid-ai.git
cd waspid-ai
docker compose up --build
```

Then open http://localhost:3000. The compose stack:

- builds the `waspid:latest` image from `containers/app/Dockerfile`
  (backend + built frontend in one container),
- mounts the Docker socket so agent sandboxes can be launched as sibling
  containers,
- persists state in `~/.waspid` on the host (the directory name is kept
  for compatibility with the upstream agent SDK — it holds Waspid state),
- mounts `./workspace` as the default agent workspace.

The same stack is available through the CLI: `waspid deploy -d`.

## Configuration

Configuration is environment-driven. The most relevant variables:

| Variable | Purpose | Default |
| --- | --- | --- |
| `OH_PERSISTENCE_DIR` | State/file-store directory | `~/.waspid` |
| `WORKSPACE_BASE` | Host directory mounted as agent workspace | `./workspace` |
| `AGENT_SERVER_IMAGE_REPOSITORY` / `AGENT_SERVER_IMAGE_TAG` | Sandbox runtime image | upstream agent-server |
| `RUNTIME` | `docker` (default), `local`, or `remote` sandboxing | docker |
| `SERVE_FRONTEND` | Serve the built SPA from the backend | `true` |
| `WEB_HOST` | Public hostname when behind a proxy | — |

LLM provider keys are configured per-user in the Settings UI, or globally
via environment variables / `waspid provider add` (see
[INSTALL.md](INSTALL.md#api-keys)).

`config.template.toml` documents the full runtime, sandbox, MCP, and
Kubernetes reference configuration.

## Databases

- **Development / single-node:** SQLite is used out of the box; no setup.
- **Production / multi-tenant:** the enterprise layer
  ([`enterprise/`](../enterprise)) targets PostgreSQL with Alembic
  migrations (`enterprise/migrations/`).

## Single node vs. multi node

The default deployment is single-node: one container running the control
plane, spawning per-conversation sandbox containers via the Docker socket.
For multi-node and Kubernetes deployment (remote runtimes, kind cluster
config under `kind/`), see [DEPLOYMENT.md](DEPLOYMENT.md).

## Enterprise features

SSO (Keycloak, Google, GitHub), multi-tenant organizations, RBAC, billing
(Stripe), and audit/analytics live in the `enterprise/` directory and run
as a separate server (`enterprise/saas_server.py`). Note its license:
[Polyform Free Trial](../enterprise/LICENSE) — usage beyond 30 days per
calendar year requires a commercial license.
