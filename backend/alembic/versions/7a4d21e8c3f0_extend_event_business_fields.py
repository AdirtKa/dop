"""extend event business fields

Revision ID: 7a4d21e8c3f0
Revises: 6c8f2a1d0b9e
Create Date: 2026-05-20 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "7a4d21e8c3f0"
down_revision: Union[str, Sequence[str], None] = "6c8f2a1d0b9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


event_hall = sa.Enum("small", "buffet", "large", name="event_hall")


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("representative", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "events",
        sa.Column("responsible_name", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "events",
        sa.Column("responsible_contact", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "events",
        sa.Column(
            "halls",
            postgresql.ARRAY(event_hall),
            nullable=False,
            server_default=sa.text("ARRAY['large']::event_hall[]"),
        ),
    )

    op.execute("UPDATE events SET halls = ARRAY[hall]::event_hall[] WHERE hall IS NOT NULL")
    op.drop_column("events", "hall")

    op.alter_column("events", "representative", server_default=None)
    op.alter_column("events", "responsible_name", server_default=None)
    op.alter_column("events", "responsible_contact", server_default=None)
    op.alter_column("events", "halls", server_default=None)


def downgrade() -> None:
    op.add_column(
        "events",
        sa.Column("hall", event_hall, nullable=False, server_default="large"),
    )
    op.execute("UPDATE events SET hall = COALESCE(halls[1], 'large'::event_hall)")
    op.alter_column("events", "hall", server_default=None)

    op.drop_column("events", "halls")
    op.drop_column("events", "responsible_contact")
    op.drop_column("events", "responsible_name")
    op.drop_column("events", "representative")
