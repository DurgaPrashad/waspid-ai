"""Workforce Architect: generates a workforce definition from an objective.

The architect is deliberately decoupled from any specific LLM client: it
receives a ``complete`` callable (messages in, text out), so production
wiring passes the user's configured LLM while tests pass a stub. The LLM
output is repaired, validated, and normalized — agents with duplicate
names are deduplicated, dangling workflow edges and unknown tools are
dropped — so callers always receive an internally consistent definition.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Callable

import json_repair
from pydantic import ValidationError

from waspid.app_server.workforce.workforce_models import (
    KNOWN_AGENT_TOOLS,
    WorkforceDefinition,
)

_logger = logging.getLogger(__name__)

ARCHITECT_SYSTEM_PROMPT = """\
You are the Waspid Workforce Architect. Given a business objective, you
design the AI workforce required to achieve it: which agents are needed,
what each one does, and how work flows between them.

Rules:
- Scale the team to the objective: a small task may need 1 agent; a full
  business may need many. Never pad the team with redundant roles.
- Every agent needs a unique short `name` (e.g. "Lead Research Agent"),
  a one-line `role`, 2-6 concrete `responsibilities`, and a complete
  `system_prompt` written in second person that would let that agent
  operate autonomously.
- `tools` must be chosen ONLY from: {tools}.
- If the team has more than one agent, include exactly one coordinating
  agent (manager/supervisor); other agents set `reports_to` to its name.
- `workflows` is a list of directed handoffs: from_agent, to_agent, and a
  `trigger` describing when the handoff happens. Every agent must appear
  in at least one workflow edge when the team has more than one agent.
- At most {max_agents} agents.

Respond with ONLY a JSON object — no markdown fences, no commentary:
{{
  "summary": "<one-paragraph description of the workforce>",
  "agents": [
    {{
      "name": "...", "role": "...",
      "responsibilities": ["..."],
      "system_prompt": "...",
      "tools": ["..."],
      "integrations": ["..."],
      "reports_to": null
    }}
  ],
  "workflows": [
    {{"from_agent": "...", "to_agent": "...", "trigger": "..."}}
  ]
}}
"""


class ArchitectError(Exception):
    """The architect could not produce a usable workforce definition."""


# Sync callable: chat messages in, assistant text out. Kept synchronous
# because litellm's sync client is the lowest-common-denominator; the
# service runs it in a worker thread.
CompletionFn = Callable[[list[dict]], str]


@dataclass
class ArchitectService:
    complete: CompletionFn
    max_attempts: int = 2

    async def generate(
        self, objective: str, max_agents: int = 12
    ) -> WorkforceDefinition:
        messages = [
            {
                'role': 'system',
                'content': ARCHITECT_SYSTEM_PROMPT.format(
                    tools=', '.join(KNOWN_AGENT_TOOLS), max_agents=max_agents
                ),
            },
            {'role': 'user', 'content': objective},
        ]
        last_error: Exception | None = None
        for attempt in range(self.max_attempts):
            try:
                text = await asyncio.to_thread(self.complete, messages)
                return self._parse(objective, text, max_agents)
            except (ArchitectError, ValidationError) as exc:
                last_error = exc
                _logger.warning(
                    'Architect attempt %d failed: %s', attempt + 1, exc
                )
                messages.append(
                    {
                        'role': 'user',
                        'content': (
                            'Your previous response was invalid '
                            f'({exc}). Respond again with ONLY the JSON object.'
                        ),
                    }
                )
        raise ArchitectError(
            f'Could not generate a workforce after {self.max_attempts} attempts: '
            f'{last_error}'
        )

    def _parse(
        self, objective: str, text: str, max_agents: int
    ) -> WorkforceDefinition:
        data = json_repair.loads(text)
        if not isinstance(data, dict):
            raise ArchitectError('LLM response was not a JSON object')
        definition = WorkforceDefinition.model_validate(
            {
                'objective': objective,
                'summary': data.get('summary', ''),
                'agents': data.get('agents', []),
                'workflows': data.get('workflows', []),
            }
        )
        return normalize_definition(definition, max_agents)


def normalize_definition(
    definition: WorkforceDefinition, max_agents: int
) -> WorkforceDefinition:
    """Make a definition internally consistent.

    - dedupe agents by name (first occurrence wins), cap at max_agents
    - drop tools the platform does not provide
    - clear reports_to / workflow edges that reference unknown agents
    """
    seen: dict[str, bool] = {}
    agents = []
    for agent in definition.agents:
        key = agent.name.strip().lower()
        if not key or key in seen or len(agents) >= max_agents:
            continue
        seen[key] = True
        agents.append(
            agent.model_copy(
                update={
                    'name': agent.name.strip(),
                    'tools': [t for t in agent.tools if t in KNOWN_AGENT_TOOLS],
                }
            )
        )
    if not agents:
        raise ArchitectError('The generated workforce contained no agents')

    names = {a.name.lower() for a in agents}
    agents = [
        a.model_copy(update={'reports_to': None})
        if a.reports_to and a.reports_to.lower() not in names
        else a
        for a in agents
    ]
    workflows = [
        e
        for e in definition.workflows
        if e.from_agent.lower() in names and e.to_agent.lower() in names
    ]
    return definition.model_copy(update={'agents': agents, 'workflows': workflows})
