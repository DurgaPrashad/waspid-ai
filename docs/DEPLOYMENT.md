<!-- Waspid AI OS -->
# Deploying Waspid

This guide covers production deployment topologies. For a quick local
or single-server install see [SELF_HOSTING.md](SELF_HOSTING.md).

## Images

- `containers/app/Dockerfile` — production image: Python backend plus
  the built frontend, served from one container (port 3000).
- `containers/dev/` — development image.
- Sandbox runtime image: `AGENT_SERVER_IMAGE_REPOSITORY:TAG`
  (the pinned upstream agent-server image; override to use a mirror).

Build: `docker compose build` or `make docker-dev`.

## Single node (recommended start)

`docker compose up -d --build` (or `waspid deploy -d`). The app
container needs:

- the Docker socket (`/var/run/docker.sock`) to launch sandbox
  containers,
- a persistent volume for state (`~/.waspid` → `/.waspid`),
- a workspace volume.

Put a TLS-terminating reverse proxy (Caddy, nginx, Traefik) in front of
port 3000 and set `WEB_HOST` to the public hostname.

## Multi node / Kubernetes

The sandbox layer is pluggable. For multi-node deployments use the
remote sandbox services (`RUNTIME=remote`,
`waspid/app_server/sandbox/remote_sandbox_*`), which place sandboxes
on remote hosts instead of the local Docker daemon.
`config.template.toml` documents Kubernetes-related settings, and
`kind/` contains a local kind-cluster configuration for testing.

## Enterprise (SaaS) deployment

The multi-tenant server (`enterprise/saas_server.py`) additionally
requires:

- PostgreSQL (migrations: `cd enterprise && alembic upgrade head`),
- Keycloak for SSO (realm template:
  `enterprise/allhands-realm-github-provider.json.tmpl`),
- Stripe keys for billing,
- the integration app credentials you intend to enable
  (GitHub app, Slack app, Jira, Linear).

See `enterprise/README.md` and note the Polyform Free Trial license.

## CI/CD

GitHub Actions workflows live in `.github/workflows/` (lint, tests,
migration checks, PR artifacts). Production rollouts are
deployment-specific; the recommended pattern is: build the app image in
CI, push to your registry, then update the compose stack or your
Kubernetes deployment to the new tag.

## Observability

- Structured logs to stdout (container-friendly).
- OpenTelemetry exporters are included (`opentelemetry-exporter-otlp`);
  point them at your collector via standard `OTEL_*` env vars.
- Health endpoint: `/health` — use it for container health checks and
  load-balancer probes.
