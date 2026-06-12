# Waspid Agent Factory

Describe a business objective in plain English — Waspid designs the AI
workforce: which agents are needed, what each one does, and how work
flows between them.

```
"Build me a real estate lead generation business"
        │
        ▼  Workforce Architect (your configured LLM)
┌──────────────────────────────────────────────────┐
│ Sales Manager Agent  ◄─ reports_to ─ Lead Research│
│ Lead Qualification → Outreach → Follow-up → CRM   │
│ + system prompts, tools, responsibilities, edges  │
└──────────────────────────────────────────────────┘
        │ save                    │ launch
        ▼                         ▼
   Blueprint library        Live Waspid runs
```

## Using the Workforce Builder

Open **Workforce Builder** (`/workforce`) in the sidebar:

1. **Describe the objective** — any role or business, not a fixed
   catalog: "HR department", "software development agency", "customer
   support for a SaaS product".
2. **Generate** — the Workforce Architect (running on the LLM you
   configured under *Settings → LLM*) returns a complete workforce
   definition. Team size scales with the objective; a small task can
   yield a single agent.
3. **Review** — the org graph shows reporting lines (solid) and
   workflow handoffs (dashed); each agent card shows role,
   responsibilities, tools, and the full system prompt.
4. **Launch** — each agent starts as a real Waspid conversation seeded
   with its generated system prompt and role. Track running agents on
   `/agents` and `/monitoring`.
5. **Save / share** — store the definition as a blueprint, clone it,
   export it as a portable `.waspid.json` file, or import one someone
   shared with you.

## How generation works

- The architect prompt (see
  `waspid/app_server/workforce/architect_service.py`) instructs the
  LLM to produce strict JSON: agents (name, role, responsibilities,
  system prompt, tools, reports_to) plus directed workflow edges with
  triggers.
- Output is repaired (`json_repair`), validated (pydantic), and
  **normalized**: duplicate agent names are dropped, tools outside the
  platform's real capability set (`terminal`, `code_editor`, `browser`,
  `web_search`, `git`, `file_storage`, `mcp`) are removed, and edges
  referencing nonexistent agents are pruned. One automatic retry feeds
  validation errors back to the model.
- Generation uses *your* provider key; there is no Waspid-side model.

## API

All endpoints under `/api/v1/workforce` (see Swagger at `/docs`):

| Endpoint | Purpose |
| --- | --- |
| `POST /generate` | Objective → workforce definition (not persisted) |
| `POST /blueprints` | Save a definition as a blueprint |
| `GET /blueprints` | List your blueprints |
| `GET /blueprints/{id}` | Fetch one |
| `DELETE /blueprints/{id}` | Delete |
| `POST /blueprints/{id}/clone` | Duplicate |
| `GET /blueprints/{id}/export` | Portable JSON (versioned) |
| `POST /blueprints/import` | Create from portable JSON |

Blueprints are stored per-user in the `workforce_blueprint` table
(migration `010`).

## Autonomous execution (the workflow runtime)

Click **Deploy & run workforce** and the workflow runtime executes the
whole team without manual launching:

1. Entry agents (no incoming edges) start immediately, each as a real
   Waspid conversation.
2. When an agent's run reaches a terminal state, a webhook-driven
   handoff processor advances the workflow: the agent's final message
   is captured into **shared workforce memory** and downstream agents
   start automatically, with upstream outputs injected into their
   kickoff. Multiple incoming edges are an AND-join — the downstream
   agent waits for all of them.
3. Failures retry automatically (2 attempts by default); exhausted
   retries fail the run, and a failed task can be manually retried from
   the dashboard, reviving the run. Stuck agents are failed by a
   timeout check (60 min default).
4. Edges marked `requires_approval` pause the run at that point: the
   downstream agent waits in **Awaiting approval** until a human clicks
   Approve on the Workflows page.
5. When every agent has finished, a final **supervisor step** runs (the
   workforce's coordinator if it has one, else a synthetic Supervisor)
   with all outputs, and its report becomes the run's final
   deliverable.

The `/workflows` page is the execution dashboard: live run status
(polled while active), per-agent task state with links into each
conversation, pause/resume/cancel, approvals, the persisted event
timeline (`workflow_started`, `agent_started`, `agent_completed`,
`agent_failed`, `agent_retrying`, `agent_timeout`, `approval_required`,
…), and the final report.

Runtime API (also in Swagger): `POST /api/v1/workforce/runs`,
`GET /runs`, `GET /runs/{id}`, `POST /runs/{id}/pause|resume|cancel`,
`POST /runs/{id}/tasks/{task_id}/approve|retry`. State lives in the
`workflow_run`, `workflow_task`, and `workflow_run_event` tables
(migration `011`).

## Current limits (honest status)

- Cancelling a run stops queued and waiting agents, but agents already
  executing in sandboxes are not killed — their late results are
  ignored.
- Cyclic workflow edges are broken deterministically at deploy time
  (dropped back-edges are recorded in the run's start event) — loops do
  not iterate.
- Dashboard liveness is polling (3–4 s), not a websocket push.
- The supervisor retries and aggregates, but does not yet *reroute*
  work to different agents, and architect feedback loops based on run
  outcomes are not built.
- Blueprint sharing is file-based (export/import); there is no hosted
  public marketplace.
