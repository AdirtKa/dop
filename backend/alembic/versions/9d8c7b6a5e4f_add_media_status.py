"""add media status

Revision ID: 9d8c7b6a5e4f
Revises: 10647957ef0c
Create Date: 2026-05-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d8c7b6a5e4f"
down_revision: Union[str, Sequence[str], None] = "10647957ef0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    media_status = sa.Enum("pending", "ready", "failed", name="media_status")
    media_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "media_files",
        sa.Column(
            "status",
            media_status,
            nullable=False,
            server_default="ready",
        ),
    )


def downgrade() -> None:
    op.drop_column("media_files", "status")
    sa.Enum("pending", "ready", "failed", name="media_status").drop(
        op.get_bind(),
        checkfirst=True,
    )
