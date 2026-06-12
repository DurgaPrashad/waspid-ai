"""Tests for the Workforce Architect service (LLM stubbed)."""

import json

import pytest

from waspid.app_server.workforce.architect_service import (
    ArchitectError,
    ArchitectService,
    normalize_definition,
)
from waspid.app_server.workforce.workforce_models import (
    AgentSpec,
    WorkflowEdge,
    WorkforceDefinition,
)

VALID_PAYLOAD = {
    'summary': 'A two-agent lead generation workforce.',
    'agents': [
        {
            'name': 'Sales Manager Agent',
            'role': 'Coordinates the team',
            'responsibilities': ['review leads', 'report results'],
            'system_prompt': 'You are the sales manager.',
            'tools': ['browser'],
            'integrations': [],
            'reports_to': None,
        },
        {
            'name': 'Lead Research Agent',
            'role': 'Finds leads',
            'responsibilities': ['search the web'],
            'system_prompt': 'You research leads.',
            'tools': ['web_search'],
            'integrations': [],
            'reports_to': 'Sales Manager Agent',
        },
    ],
    'workflows': [
        {
            'from_agent': 'Lead Research Agent',
            'to_agent': 'Sales Manager Agent',
            'trigger': 'leads collected',
        }
    ],
}


def make_architect(responses):
    """Architect whose LLM returns the queued responses in order."""
    queue = list(responses)

    def complete(messages):
        return queue.pop(0)

    return ArchitectService(complete=complete)


@pytest.mark.asyncio
async def test_generate_parses_valid_json():
    architect = make_architect([json.dumps(VALID_PAYLOAD)])
    definition = await architect.generate('Build a lead gen business')
    assert definition.objective == 'Build a lead gen business'
    assert [a.name for a in definition.agents] == [
        'Sales Manager Agent',
        'Lead Research Agent',
    ]
    assert definition.workflows[0].trigger == 'leads collected'


@pytest.mark.asyncio
async def test_generate_repairs_json_in_markdown_fences():
    text = '```json\n' + json.dumps(VALID_PAYLOAD) + '\n```'
    architect = make_architect([text])
    definition = await architect.generate('objective')
    assert len(definition.agents) == 2


@pytest.mark.asyncio
async def test_generate_retries_then_succeeds():
    architect = make_architect(['[]', json.dumps(VALID_PAYLOAD)])
    definition = await architect.generate('objective')
    assert len(definition.agents) == 2


@pytest.mark.asyncio
async def test_generate_fails_after_max_attempts():
    architect = make_architect(['not json at all []', '[]'])
    with pytest.raises(ArchitectError):
        await architect.generate('objective')


@pytest.mark.asyncio
async def test_generate_rejects_empty_workforce():
    payload = {'summary': 'nothing', 'agents': [], 'workflows': []}
    architect = make_architect([json.dumps(payload), json.dumps(payload)])
    with pytest.raises(ArchitectError):
        await architect.generate('objective')


def _definition(agents, workflows=()):
    return WorkforceDefinition(
        objective='x', agents=list(agents), workflows=list(workflows)
    )


def test_normalize_dedupes_agents_and_caps_count():
    agents = [
        AgentSpec(name='A', role='r', system_prompt='p'),
        AgentSpec(name='a', role='r', system_prompt='p'),  # dup, case-insensitive
        AgentSpec(name='B', role='r', system_prompt='p'),
        AgentSpec(name='C', role='r', system_prompt='p'),
    ]
    result = normalize_definition(_definition(agents), max_agents=2)
    assert [a.name for a in result.agents] == ['A', 'B']


def test_normalize_drops_unknown_tools():
    agents = [
        AgentSpec(
            name='A',
            role='r',
            system_prompt='p',
            tools=['browser', 'quantum_blockchain'],
        )
    ]
    result = normalize_definition(_definition(agents), max_agents=10)
    assert result.agents[0].tools == ['browser']


def test_normalize_clears_dangling_reports_to_and_edges():
    agents = [
        AgentSpec(name='A', role='r', system_prompt='p', reports_to='Ghost'),
        AgentSpec(name='B', role='r', system_prompt='p', reports_to='A'),
    ]
    workflows = [
        WorkflowEdge(from_agent='A', to_agent='B'),
        WorkflowEdge(from_agent='A', to_agent='Ghost'),
    ]
    result = normalize_definition(_definition(agents, workflows), max_agents=10)
    assert result.agents[0].reports_to is None
    assert result.agents[1].reports_to == 'A'
    assert len(result.workflows) == 1
    assert result.workflows[0].to_agent == 'B'


def test_normalize_raises_when_no_agents_remain():
    with pytest.raises(ArchitectError):
        normalize_definition(_definition([]), max_agents=5)
