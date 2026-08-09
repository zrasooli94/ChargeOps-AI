"""baseline existing schema"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import VECTOR
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260809_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS vector"
    )

    op.create_table(
        "stations",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "station_id",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "charger_model",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "location",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "latitude",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "longitude",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "station_id",
        ),
    )

    op.create_index(
        "ix_stations_station_id",
        "stations",
        ["station_id"],
    )

    op.create_table(
        "incidents",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "station_id",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "issue",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "confidence",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "summary",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "likely_causes",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "diagnostic_steps",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "needs_human_escalation",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["stations.station_id"],
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_incidents_station_id",
        "incidents",
        ["station_id"],
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "document_key",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "embedding",
            VECTOR(1536),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "document_key",
        ),
    )

    op.create_index(
        "ix_knowledge_chunks_document_key",
        "knowledge_chunks",
        ["document_key"],
    )

    op.create_index(
        "ix_knowledge_chunks_embedding_hnsw",
        "knowledge_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={
            "m": 16,
            "ef_construction": 64,
        },
        postgresql_ops={
            "embedding": "vector_cosine_ops",
        },
    )


def downgrade() -> None:
    op.drop_index(
        "ix_knowledge_chunks_embedding_hnsw",
        table_name="knowledge_chunks",
    )

    op.drop_table(
        "knowledge_chunks"
    )

    op.drop_table(
        "incidents"
    )

    op.drop_table(
        "stations"
    )