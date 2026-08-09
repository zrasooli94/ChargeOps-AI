"""add knowledge document ingestion"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260809_02"
down_revision: str | None = "20260809_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_documents",
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
            "source_filename",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "media_type",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "sha256",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "chunk_count",
            sa.Integer(),
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
        sa.UniqueConstraint(
            "sha256",
        ),
    )

    op.create_index(
        "ix_knowledge_documents_document_key",
        "knowledge_documents",
        ["document_key"],
    )

    op.create_index(
        "ix_knowledge_documents_sha256",
        "knowledge_documents",
        ["sha256"],
    )

    op.add_column(
        "knowledge_chunks",
        sa.Column(
            "knowledge_document_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "knowledge_chunks",
        sa.Column(
            "chunk_index",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "knowledge_chunks",
        sa.Column(
            "page_number",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "knowledge_chunks",
        sa.Column(
            "content_hash",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.add_column(
        "knowledge_chunks",
        sa.Column(
            "char_count",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_knowledge_chunks_knowledge_document_id",
        "knowledge_chunks",
        "knowledge_documents",
        [
            "knowledge_document_id"
        ],
        [
            "id"
        ],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_knowledge_chunks_knowledge_document_id",
        "knowledge_chunks",
        [
            "knowledge_document_id"
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_knowledge_chunks_knowledge_document_id",
        table_name="knowledge_chunks",
    )

    op.drop_constraint(
        "fk_knowledge_chunks_knowledge_document_id",
        "knowledge_chunks",
        type_="foreignkey",
    )

    op.drop_column(
        "knowledge_chunks",
        "char_count",
    )

    op.drop_column(
        "knowledge_chunks",
        "content_hash",
    )

    op.drop_column(
        "knowledge_chunks",
        "page_number",
    )

    op.drop_column(
        "knowledge_chunks",
        "chunk_index",
    )

    op.drop_column(
        "knowledge_chunks",
        "knowledge_document_id",
    )

    op.drop_table(
        "knowledge_documents"
    )