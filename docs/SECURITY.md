# Waspid Security Report

Date: 2026-06-12. Scope: the Waspid platform additions (agent factory,
workflow runtime, Integration Hub, CLI) plus the platform's existing
auth/secrets architecture. This is an internal engineering review, not
a third-party penetration test.

## Authentication & authorization model

| Deployment | Authentication | Authorization |
| --- | --- | --- |
| Self-hosted (OSS) | Single-user; session API keys scope sandbox callbacks (`X-Session-API-Key`) | All resources belong to the single user (`user_id = NULL`) |
| Enterprise (SaaS, `enterprise/`) | Keycloak (OIDC) — Google/GitHub/Microsoft SSO; bearer tokens; per-user API keys | Organizations, roles, and member management in the enterprise layer; every core API resolves the caller through `user_auth.get_user_id()` |

Tenant separation for all new resources is enforced at the query layer:
blueprints, workflow runs, integration connections, and tool-call logs
are filtered by `user_id` in every read/write (`WHERE user_id = :caller`).
Webhook-driven internals (`get_run_any_user`, conversation→task lookup)
run only in server-side callback contexts, never from request handlers.
Covered by tests: `test_security_hardening.py`,
`test_workforce_blueprint_service.py`, `test_integration_hub.py`.

## Secrets handling

- Integration Hub credentials are **encrypted at rest** (JWE via the
  platform JWT service, `StoredSecretStr`) and **never returned by any
  API** (stripped before serialization).
- Custom secrets (Settings → Secrets) flow control-plane → sandbox
  only; raw values never pass through the browser or SDK clients.
- The CLI stores provider keys in `~/.waspid/waspid.env` with mode
  `0600`.
- LLM keys are masked in settings responses (platform behavior).

## Findings from this review

| # | Severity | Finding | Status |
| --- | --- | --- | --- |
| 1 | **High** | **SSRF via webhook-type connections**: Discord/generic-webhook URLs are user-supplied and POSTed server-side; could target internal services or cloud metadata (169.254.169.254, metadata.google.internal). | **Fixed** — `url_guard.py` enforces https + blocks loopback/private/link-local/metadata targets, validated at connection creation *and* re-checked at every execution (DNS may change between save and use). |
| 2 | Medium | No per-user rate limit on LLM-backed generation or outbound tool execution (cost amplification / provider abuse; the global limiter is per-IP only). | **Fixed** — sliding-window per-user limits: 10 generations/min, 30 tool executions/min (HTTP 429). |
| 3 | Medium | Unbounded workforce definitions accepted on import/save (storage and execution DoS: unlimited agents, unlimited prompt size). | **Fixed** — hard caps: ≤100 agents, ≤500 edges, ≤20 kB system prompts, ≤4 kB objective; oversized payloads are rejected, not truncated. |
| 4 | Low | `StoredSecretStr.process_result_param` is dead code (SQLAlchemy calls `process_result_value`) — reads return raw ciphertext, and naive callers might store/compare it. | **Mitigated** in Hub code (`_secret_value` decrypts explicitly, tolerant of both behaviors). Upstream decorator fix recommended. |
| 5 | Low | Security-relevant actions lacked audit trail in the core (OSS) server. | **Improved** — structured audit log (`waspid.audit` logger): connection create/delete, workflow run start; plus persisted domain logs (workflow_run_event, tool_call_log with per-run/agent attribution). |
| 6 | Info | Cancelling a run does not kill in-flight sandboxes; their late results are discarded by the engine's idempotency check. | Accepted for now; documented. |

## Existing controls inventory

- Sandbox isolation: one container per agent run; sandbox→server auth
  via per-session API keys; secrets fetched server-side per sandbox.
- Global per-IP rate-limit middleware; CORS configuration; JWT/JWE
  services for tokens and encrypted storage.
- Dependency pins for known CVEs are tracked in `pyproject.toml`
  (authlib, orjson, urllib3 comments name the CVEs).
- CI: lint, type checks, unit tests, migration-conflict checks.

## Compliance readiness (honest posture)

| Framework | Posture |
| --- | --- |
| SOC 2 | Architecture supports the control families: SSO (Keycloak), role-based org membership, audit/event trails (enterprise analytics + workflow/tool logs), encryption at rest for credentials, change management via CI. **Formal policies, evidence collection, and an external audit are not in place.** |
| GDPR | Per-user data scoping makes subject access/deletion tractable; data minimization holds (credentials encrypted, never echoed). **A data-deletion endpoint covering all stores, a DPA template, and a records-of-processing doc are still needed.** |
| HIPAA | Not ready. No BAA, no PHI-specific controls. Architecture (tenant isolation, encryption, audit) is a foundation, nothing more. |

## Remaining risks

1. **DNS rebinding**: the SSRF guard resolves hostnames at validation
   time; a hostile DNS server could still rebind between the guard's
   resolution and httpx's. Full mitigation needs a pinned-IP transport.
2. **In-memory rate limits are per-process** — multi-replica
   deployments must also enforce limits at the gateway.
3. **Live integration paths** (workflow handoff processor, real
   provider APIs) are mock-tested but not yet exercised end-to-end on a
   running deployment.
4. **OSS single-user mode** has no RBAC by design; anyone with access
   to the port has full control — deploy behind authentication or use
   the enterprise server for multi-user setups.
5. Per-agent tool allow/deny lists are not yet enforced; any agent in a
   run can trigger any connected provider via workflow actions.
6. Backend pre-commit (ruff/mypy) gating must run in CI for the new
   modules (not runnable on the authoring machine).
