"""Add workflow runtime tables (runs, tasks, run events)

Revision ID: 011
Revises: 010
Create Date: 2026-06-12 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'workflow_run',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('blueprint_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('definition', sa.JSON(), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('final_output', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_workflow_run_user_id'), 'workflow_run', ['user_id'], unique=False
    )
    op.create_index(
        op.f('ix_workflow_run_status'), 'workflow_run', ['status'], unique=False
    )
    op.create_index(
        op.f('ix_workflow_run_created_at'),
        'workflow_run',
        ['created_at'],
        unique=False,
    )

    op.create_table(
        'workflow_task',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('run_id', sa.UUID(), nullable=False),
        sa.Column('agent_name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=True),
        sa.Column('max_attempts', sa.Integer(), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=True),
        sa.Column('approved', sa.Boolean(), nullable=True),
        sa.Column('is_aggregation', sa.Boolean(), nullable=True),
        sa.Column('output', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_workflow_task_run_id'), 'workflow_task', ['run_id'], unique=False
    )
    op.create_index(
        op.f('ix_workflow_task_status'), 'workflow_task', ['status'], unique=False
    )
    op.create_index(
        op.f('ix_workflow_task_conversation_id'),
        'workflow_task',
        ['conversation_id'],
        unique=False,
    )

    op.create_table(
        'workflow_run_event',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('run_id', sa.UUID(), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('agent_name', sa.String(), nullable=True),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_workflow_run_event_run_id'),
        'workflow_run_event',
        ['run_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_workflow_run_event_created_at'),
        'workflow_run_event',
        ['created_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table('workflow_run_event')
    op.drop_table('workflow_task')
    op.drop_table('workflow_run')
