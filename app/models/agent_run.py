from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
)
from sqlalchemy.dialects.postgresql import (
    UUID as PGUUID,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.database import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    thread_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    station_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    user_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    answer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    used_tools: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    trace: Mapped[
        list[dict[str, Any]]
    ] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    approval_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    approval_decision: Mapped[
        bool | None
    ] = mapped_column(
        Boolean,
        nullable=True,
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    completed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )