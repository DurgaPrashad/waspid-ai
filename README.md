<!-- Waspid AI OS -->
<a name="readme-top"></a>

<div align="center">
  <h1 align="center" style="border-bottom: none">Waspid</h1>
  <h3 align="center" style="border-bottom: none">The Enterprise AI Workforce Operating System</h3>
</div>

<div align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/LICENSE-MIT-20B2AA?style=for-the-badge" alt="MIT License"></a>
  <a href="enterprise/LICENSE"><img src="https://img.shields.io/badge/Enterprise-Polyform_Free_Trial-444?style=for-the-badge" alt="Enterprise License"></a>
</div>

<hr>

**Waspid** is an enterprise AI workforce operating system. It lets businesses
build, deploy, orchestrate, and scale AI agents across voice, browser
automation, workflows, APIs, customer support, sales, and enterprise
operations — under one control plane.

Waspid is designed for organizations that want to run AI as infrastructure,
not as a chatbot:

- **AI workforce dashboard** — deploy, monitor, and manage fleets of agents
  the way you manage employees.
- **Workflow orchestration** — long-running, multi-step, multi-agent
  workflows with retries, audit trails, and observability.
- **Voice + browser automation** — agents that can take phone calls,
  navigate the web, fill forms, drive CRMs, and complete real-world
  business tasks.
- **Multi-tenant by design** — organizations, roles, permissions, isolated
  data, and per-tenant integrations.
- **Enterprise integrations** — Slack, Jira, Linear, GitHub, GitLab,
  Bitbucket, Keycloak, Stripe, and a pluggable connector framework.
- **Realtime, observable, auditable** — websocket-streamed events,
  structured logs, OpenTelemetry, analytics.

## Repository structure

| Path | Purpose |
| --- | --- |
| [`waspid/`](waspid) | Core Python control plane (FastAPI). Imports the pinned upstream agent SDK as the agent runtime (see [CREDITS.md](CREDITS.md)). |
| [`enterprise/`](enterprise) | Multi-tenant SaaS layer: auth, billing, orgs, integrations, sharing. |
| [`frontend/`](frontend) | React 19 + React Router 7 SPA — workforce dashboard, conversation UI, settings. |
| [`waspid-ui/`](waspid-ui) | Shared React component library (`@waspid/ui`). |
| [`containers/`](containers) | Production and development Dockerfiles. |
| [`enterprise/migrations/`](enterprise/migrations) | Alembic migrations for the SaaS schema. |
| [`config.template.toml`](config.template.toml) | Reference configuration for runtime, sandbox, MCP, and Kubernetes. |

## Running locally

The fastest path:

```bash
make build
make run
```

Or with Docker: `docker compose up --build`, then open
http://localhost:3000.

Once installed, the `waspid` CLI provides `waspid start`, `waspid dev`,
`waspid doctor`, `waspid provider add <provider> <key>`, and more — see
[docs/CLI.md](docs/CLI.md).

For full setup instructions per OS (macOS, Linux, Windows WSL, Dev Container,
Docker), see [Development.md](Development.md).

## Documentation

| Guide | Contents |
| --- | --- |
| [docs/INSTALL.md](docs/INSTALL.md) | Installation and provider API keys |
| [docs/SELF_HOSTING.md](docs/SELF_HOSTING.md) | Self-hosting with Docker Compose |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production, multi-node, enterprise deployment |
| [docs/CLI.md](docs/CLI.md) | The `waspid` command-line interface |
| [docs/API.md](docs/API.md) | REST/WebSocket API overview |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and roadmap |
| [docs/AGENT_FACTORY.md](docs/AGENT_FACTORY.md) | Workforce Builder: objective → AI workforce |
| [docs/AGENTS_GUIDE.md](docs/AGENTS_GUIDE.md) | Configuring and prompting agents |
| [docs/WORKFLOWS_GUIDE.md](docs/WORKFLOWS_GUIDE.md) | Orchestration: today and planned |
| [docs/INTEGRATIONS_GUIDE.md](docs/INTEGRATIONS_GUIDE.md) | Integration Hub, git providers, chat-ops, MCP |
| [docs/SECURITY.md](docs/SECURITY.md) | Security report, controls, compliance posture |

## Built on an open-source agent runtime

Waspid's agent runtime is an MIT-licensed open-source agent SDK, consumed as
pinned packages. Waspid extends that runtime with the enterprise workforce,
orchestration, multi-tenancy, voice, and operations layers required to run
AI as production infrastructure. Full upstream attribution is in
[CREDITS.md](CREDITS.md).

The internal Python package directory is named `waspid/` to preserve
SDK compatibility. This is intentional and will not change in the near term.

## Licensing

- The MIT license in [LICENSE](LICENSE) covers everything **outside** the
  `enterprise/` directory.
- The code in [`enterprise/`](enterprise) is licensed under the
  [Polyform Free Trial License](enterprise/LICENSE). It is **not** an open
  source license — usage is limited to 30 days per calendar year without a
  commercial license.
- Upstream attribution: the agent SDK and runtime packages consumed by
  Waspid are MIT-licensed by their original project — see
  [CREDITS.md](CREDITS.md) for full attribution.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow, PR title
conventions, and tooling expectations. For background on the underlying
agent runtime, see [CREDITS.md](CREDITS.md).
