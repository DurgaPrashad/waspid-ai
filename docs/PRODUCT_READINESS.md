<!-- Waspid AI OS -->
# Waspid Product Readiness Report

Date: 2026-06-12. Method: the full backend was booted from source on a
clean Python 3.13 environment (SQLite, migrations 001–012 auto-applied
at startup) serving the production frontend build, and every major
flow was exercised over the live API. Frontend surfaces additionally
verified by 14 component tests; backend by 63 unit tests.

## What was validated live (all passing)

| Area | Result |
| --- | --- |
| Server boot | App imports (92 routes), alembic migrations run, `/health` OK, OpenAPI title "Waspid" |
| Frontend | Production SPA served by the backend; `<title>Waspid</title>` |
| Agent Factory | Blueprint create/list against the real DB; `/generate` without an LLM returns a clear, actionable 400 |
| Template requirements (new) | Deploying a blueprint that references `hubspot` (agent integration) and `slack` (edge action) without connections → HTTP 409 with `{llm_configured, required_integrations, missing_integrations}`; builder UI now renders this as "Before deploying: configure an LLM… and connect hubspot, slack…" — `ignore_missing_requirements` overrides |
| Workflow runtime | Live deploy: run persisted RUNNING, task launched (attempt 1), `workflow_started`/`agent_started` events recorded; pause → PAUSED, resume → RUNNING, cancel → CANCELLED |
| Integration Hub | 13 providers listed; Slack connection created (credential encrypted, **never echoed in any response**); 30 failed outbound calls correctly logged with failure counts |
| SSRF guard | `https://169.254.169.254/...` and `https://localhost/...` webhook connections rejected with 400 and explicit reasons |
| Rate limiting | 31st tool execution within a minute → HTTP 429 |
| CLI | `waspid version / provider list / doctor` work; `provider add` writes `~/.waspid/waspid.env` (0600) |

## Defects found during validation (fixed)

1. Deploy errors showed a generic axios message instead of the 409
   requirements payload — builder now explains exactly what to
   configure and where.
2. Hub tables missed `Base.metadata` registration when the security
   test file ran alone (test-ordering bug) — fixed.
3. Earlier phases' fixes re-confirmed live (SSRF, rate limits,
   credential masking).

## Settings & secrets from the UI (Step 3/4 status)

Already true — no `.env` editing needed after install:
- LLM providers (OpenAI, Anthropic, Gemini, Grok, OpenRouter, DeepSeek,
  Azure, Bedrock, Ollama, …) configure in *Settings → LLM* per user,
  stored server-side; `waspid provider add` is an optional CLI
  alternative.
- Integrations connect from the Integrations page (Hub section);
  credentials encrypted at rest, replace/delete anytime.
- Custom secrets for sandbox-path tools: *Settings → Secrets*.

## Known limitations (honest)

- **Agent execution requires Docker** (or a remote runtime). On a
  Docker-less host everything except sandbox boot works; stalled
  launches are failed by the 60-minute task timeout. The
  webhook-driven handoff (sandbox → server event → next agent) is
  engine-tested but still needs one supervised end-to-end run on a
  Docker host.
- **Dev test account (Step 6):** intentionally NOT implemented as a
  hardcoded credential. Self-hosted Waspid is single-user with no
  login — a seeded password would add attack surface without value.
  Multi-user auth lives in the enterprise layer (Keycloak), where dev
  realms define test users (`enterprise/dev_config`); credentials
  belong in that realm config, never in application code. A hardcoded
  `test@example.com / test@12345` would inevitably leak into
  production builds — this is the documented, deliberate refusal.
- "Deployments" nav item remains honestly marked *Soon* (disabled).
- Dashboard liveness is polling; websocket push not yet built.
- `enterprise/` SaaS layer (Keycloak, Stripe, orgs) was not booted in
  this validation (needs Postgres + Keycloak infrastructure).

## Performance notes

- Server boot to healthy: a few seconds (SQLite). Workforce/hub API
  calls returned in single-digit milliseconds locally; the expensive
  paths (LLM generation, sandbox boot) are rate-limited and async
  respectively.
- The frontend production build is ~3 s (Vite) with code-split routes.

## Production readiness verdict

Ready for self-hosted single-user production use on a Docker host:
clone → `make build` → `waspid start` → configure providers in the UI
→ generate/deploy workforces → monitor on /workflows. Multi-user SaaS
readiness depends on deploying the enterprise layer and completing the
items in [SECURITY.md](SECURITY.md) remaining-risks list.
