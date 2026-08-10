import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260810_03"
down_revision = "20260809_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "thread_id",
            sa.String(
                length=36
            ),
            nullable=False,
        ),
        sa.Column(
            "station_id",
            sa.String(
                length=50
            ),
            nullable=False,
        ),
        sa.Column(
            "user_message",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(
                length=30
            ),
            nullable=False,
        ),
        sa.Column(
            "answer",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "used_tools",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
        ),
        sa.Column(
            "trace",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
        ),
        sa.Column(
            "approval_required",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "approval_decision",
            sa.Boolean(),
            nullable=True,
        ),
        sa.Column(
            "model",
            sa.String(
                length=100
            ),
            nullable=False,
        ),
        sa.Column(
            "latency_ms",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(
                timezone=True
            ),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        "ix_agent_runs_thread_id",
        "agent_runs",
        [
            "thread_id",
        ],
    )

    op.create_index(
        "ix_agent_runs_station_id",
        "agent_runs",
        [
            "station_id",
        ],
    )

    op.create_index(
        "ix_agent_runs_status",
        "agent_runs",
        [
            "status",
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_runs_status",
        table_name="agent_runs",
    )

    op.drop_index(
        "ix_agent_runs_station_id",
        table_name="agent_runs",
    )

    op.drop_index(
        "ix_agent_runs_thread_id",
        table_name="agent_runs",
    )

    op.drop_table(
        "agent_runs"
    )