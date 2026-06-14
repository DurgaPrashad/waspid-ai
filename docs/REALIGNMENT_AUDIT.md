<!-- Waspid AI OS -->
# Waspid Realignment Audit & Redesign Report

Date: 2026-06-12. Scope: full product audit against the target
identity — *Enterprise AI Workforce Operating System*, not a chat app,
not a coding assistant, not a modified Waspid instance.

## 1. What already behaves like Waspid

- **Workforce-first surfaces**: Workforce Builder (architect → org
  graph → deploy), Workflows execution dashboard (runs, approvals,
  timelines, final deliverables), Agents fleet view, Monitoring,
  Integration Hub with tool registry and observability.
- **Branding**: UI, i18n (17 languages), metadata, FastAPI title, CLI,
  Docker, docs — all Waspid. SDK wire-protocol names are intentionally
  retained (documented in ARCHITECTURE.md).
- **Enterprise IA**: sidebar nav (Workforce / Operations / Platform
  groups) with honest "Soon" gating; settings entirely UI-driven
  (providers, integrations, secrets — no .env editing).
- **Platform plumbing**: requirements gating at deploy, rate limits,
  SSRF guard, encrypted credentials, audit/event logs.

## 2. What still behaved like Waspid (and what changed now)

| Legacy pattern | Status |
| --- | --- |
| **`/` opened on conversation dispatch** (repo connector + "new conversation" as the lead action) | **Fixed**: `/` is now the **Workforce Command Center** — a "What would you like to build?" prompt feeding the Architect, command cards for the platform surfaces, readiness grid, recent operations. Single-agent dispatch is demoted to a secondary "Direct agent dispatch" section (it remains the unit operation under every workforce — removing it would break real workflows, so it is deliberately kept, not hidden). |
| Home title "Operations Center" with generic copy | **Fixed**: "Workforce Command Center", OS-positioning copy; nav label updated. |
| Builder not reachable with a prefilled goal | **Fixed**: Command Center hands off via `?objective=`. |
| **Dark developer/terminal aesthetic** | **Partially addressed — deliberately.** The premium cream/beige/charcoal palette ships as a complete token set (`[data-theme='waspid-light']` in `styles/tokens.css`). It is *not* yet the default: ~128 components carry hardcoded dark-theme colors (`text-white`, `bg-[#050505]`, …) that would become unreadable on cream without a per-surface migration and visual QA. Flipping blind would ship a broken product. Migration plan below. |
| Conversation screen (terminal, VS Code tab, diff viewer) | **Kept intentionally.** This is the *agent run* view — the real execution surface for every workforce agent. It is runtime infrastructure, not a chat-first assumption. |

## 3. What should be removed — legacy removal report

- Conversation-first home layout — **removed** (this phase).
- `CNAME`, Waspid URLs/branding, README garbage — removed in
  earlier phases.
- No dead routes found: all 38 routes resolve to real surfaces; the
  only disabled nav item ("Deployments") is honestly gated, not a
  broken link.
- Speculative workflow types (`WorkflowRunSummary` contract with no
  backend) — already replaced by the real runtime API types.

## 4. What should be redesigned next (plan, in order)

1. **Theme migration to Waspid Premium (light)** — sweep the ~128
   files with hardcoded colors onto semantic tokens
   (`text-content`/`bg-base…`), surface by surface (shell → command
   center → builder → workflows → settings → conversation last), with
   browser-level visual QA per step; then set
   `data-theme="waspid-light"` as default. The palette, mapping, and
   activation switch are ready in `styles/tokens.css`.
2. **Marketing site** (Platform / Marketplace / Enterprise / Docs /
   Contact / Careers top navigation + landing page with "Build
   Workforce" CTA): this is a separate public website, not the
   authenticated app — recommend a standalone site repo using the
   landing copy already drafted in README/this doc. The in-app
   equivalent of "landing" is the Command Center; the SaaS login page
   is the natural place for the hero copy when the marketing site
   does not exist.
3. **Marketplace surface**: dedicated route for the blueprint library
   with sharing (currently file-based export/import inside the
   builder).
4. Websocket push for dashboards; per-agent tool permissions; OAuth
   redirect flows (carried from SECURITY/READINESS reports).

## Validation of this phase

- Command Center renders the prompt, example objectives, and command
  cards; submitting navigates to `/workforce?objective=…` and the
  builder prefills it (component tests).
- All existing home/builder/workflows/hub tests pass; production
  build clean; no backend changes.
