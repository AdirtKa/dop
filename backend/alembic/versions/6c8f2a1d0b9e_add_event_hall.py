"""add event hall

Revision ID: 6c8f2a1d0b9e
Revises: 2b7e91c4d6a3
Create Date: 2026-05-20 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6c8f2a1d0b9e"
down_revision: Union[str, Sequence[str], None] = "2b7e91c4d6a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    event_hall = sa.Enum("small", "buffet", "large", name="event_hall")
    event_hall.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "events",
        sa.Column(
            "hall",
            event_hall,
            nullable=False,
            server_default="large",
        ),
    )
    op.alter_column("events", "hall", server_default=None)


def downgrade() -> None:
    op.drop_column("events", "hall")

    event_hall = sa.Enum("small", "buffet", "large", name="event_hall")
    event_hall.drop(op.get_bind(), checkfirst=True)
