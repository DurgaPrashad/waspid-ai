# Waspid AI OS
"""Add integration hub tables (connections, tool call log)

Revision ID: 012
Revises: 011
Create Date: 2026-06-12 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'integration_connection',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('credential', sa.String(), nullable=False),
        sa.Column('base_url', sa.String(), nullable=True),
        sa.Column('last_check_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_check_ok', sa.Boolean(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_integration_connection_user_id'),
        'integration_connection',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_integration_connection_provider'),
        'integration_connection',
        ['provider'],
        unique=False,
    )

    op.create_table(
        'tool_call_log',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('tool', sa.String(), nullable=False),
        sa.Column('ok', sa.Boolean(), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('run_id', sa.UUID(), nullable=True),
        sa.Column('agent_name', sa.String(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_tool_call_log_user_id'), 'tool_call_log', ['user_id'], unique=False
    )
    op.create_index(
        op.f('ix_tool_call_log_provider'), 'tool_call_log', ['provider'], unique=False
    )
    op.create_index(
        op.f('ix_tool_call_log_run_id'), 'tool_call_log', ['run_id'], unique=False
    )
    op.create_index(
        op.f('ix_tool_call_log_created_at'),
        'tool_call_log',
        ['created_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table('tool_call_log')
    op.drop_table('integration_connection')
