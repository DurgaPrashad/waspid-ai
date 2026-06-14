# Waspid AI OS
"""Create verified_models table.

Revision ID: 098
Revises: 097
Create Date: 2026-02-26 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '098'
down_revision: Union[str, None] = '097'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create verified_models table and seed with current model list."""
    op.create_table(
        'verified_models',
        sa.Column('id', sa.Integer, sa.Identity(), primary_key=True),
        sa.Column('model_name', sa.String(255), nullable=False),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column(
            'is_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true'),
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        sa.UniqueConstraint(
            'model_name', 'provider', name='uq_verified_model_provider'
        ),
    )

    op.create_index(
        'ix_verified_models_provider',
        'verified_models',
        ['provider'],
    )
    op.create_index(
        'ix_verified_models_is_enabled',
        'verified_models',
        ['is_enabled'],
    )

    # Seed with current waspid provider models
    models = [
        ('claude-opus-4-5-20251101', 'waspid'),
        ('claude-sonnet-4-5-20250929', 'waspid'),
        ('gpt-5.2-codex', 'waspid'),
        ('gpt-5.2', 'waspid'),
        ('minimax-m2.5', 'waspid'),
        ('gemini-3-pro-preview', 'waspid'),
        ('gemini-3-flash-preview', 'waspid'),
        ('deepseek-chat', 'waspid'),
        ('devstral-medium-2512', 'waspid'),
        ('kimi-k2-0711-preview', 'waspid'),
        ('qwen3-coder-480b', 'waspid'),
    ]

    for model_name, provider in models:
        op.execute(
            sa.text(
                """
                INSERT INTO verified_models (model_name, provider)
                VALUES (:model_name, :provider)
                """
            ).bindparams(model_name=model_name, provider=provider)
        )


def downgrade() -> None:
    """Drop verified_models table."""
    op.drop_index('ix_verified_models_is_enabled', table_name='verified_models')
    op.drop_index('ix_verified_models_provider', table_name='verified_models')
    op.drop_table('verified_models')
