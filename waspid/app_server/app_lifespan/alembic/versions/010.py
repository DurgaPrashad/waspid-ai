"""Add workforce_blueprint table for the agent factory

Revision ID: 010
Revises: 009
Create Date: 2026-06-12 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'workforce_blueprint',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('definition', sa.JSON(), nullable=True),
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
        op.f('ix_workforce_blueprint_user_id'),
        'workforce_blueprint',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_workforce_blueprint_created_at'),
        'workforce_blueprint',
        ['created_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_workforce_blueprint_created_at'), table_name='workforce_blueprint'
    )
    op.drop_index(
        op.f('ix_workforce_blueprint_user_id'), table_name='workforce_blueprint'
    )
    op.drop_table('workforce_blueprint')
