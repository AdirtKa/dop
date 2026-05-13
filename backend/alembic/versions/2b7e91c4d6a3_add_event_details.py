"""add event details

Revision ID: 2b7e91c4d6a3
Revises: 9d8c7b6a5e4f
Create Date: 2026-05-13 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2b7e91c4d6a3"
down_revision: Union[str, Sequence[str], None] = "9d8c7b6a5e4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column(
            "details",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
    )
    op.alter_column("events", "details", server_default=None)


def downgrade() -> None:
    op.drop_column("events", "details")
