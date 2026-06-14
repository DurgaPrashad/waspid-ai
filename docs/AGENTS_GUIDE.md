<!-- Waspid AI OS -->
# Waspid Agents Guide

## What an agent is in Waspid

An agent run ("conversation") is an autonomous worker executing in an
isolated sandbox with its own workspace, tools (terminal, editor,
browser), and event stream. The **Agents** page (`/agents`) shows your
active fleet; **Monitoring** (`/monitoring`) shows every run with model,
cost, and lifecycle state.

Waspid supports two agent kinds:

- **Native agents** — powered by the built-in SDK runtime with your
  configured LLM provider.
- **ACP agents** — external agent CLIs (Claude Code, Codex, Gemini CLI,
  or custom commands) driven through the Agent Client Protocol.

## Configuring agents

*Settings → Agent* controls the default agent, sub-agent support, and
runtime options. *Settings → LLM* selects provider and model (see
[INSTALL.md](INSTALL.md#api-keys)).

## Customizing agents per repository

### Microagents

Microagents are Markdown files that inject domain knowledge into the
agent's context:

- **Repository microagents:** `.waspid/microagents/*.md` in your repo
  (the directory name is kept for SDK compatibility).
- Files without frontmatter are always loaded; files with a `triggers:`
  list in YAML frontmatter load only when a user message matches a
  trigger keyword.

```markdown
---
triggers:
- deploy
---
Use `make deploy-staging`; production deploys require a release tag.
```

A useful first step in any repo: ask the agent to write a repo
description (including how to build and test) into
`.waspid/microagents/repo.md`.

### Setup script

Add `.waspid/setup.sh` to your repository and Waspid runs it at the
start of every conversation — install dependencies, export variables,
seed data.

## Prompting agents effectively

- Be specific about the outcome and where the change should land
  (file paths, branch names).
- Point the agent at relevant files rather than describing them.
- Prefer several small, verifiable tasks over one broad task.
- Tell the agent how to verify its work (test command, expected output).

## Best practices for fleets

- Give each run a narrow objective; use Monitoring to track cost per run.
- Keep secrets in *Settings → Secrets* — they are injected into sandboxes
  server-side and never pass through the browser.
- Use webhooks (event callbacks) to route run events into your own
  systems.
