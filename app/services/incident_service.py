from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.schemas.analysis import ChargingIssueAnalysis


async def create_incident(
    session: AsyncSession,
    station_id: str,
    issue: str,
    analysis: ChargingIssueAnalysis,
) -> Incident:
    incident = Incident(
        station_id=station_id,
        issue=issue,
        category=analysis.category,
        severity=analysis.severity,
        confidence=analysis.confidence,
        summary=analysis.summary,
        likely_causes=analysis.likely_causes,
        diagnostic_steps=[
            step.model_dump()
            for step in analysis.diagnostic_steps
        ],
        needs_human_escalation=(
            analysis.needs_human_escalation
        ),
        status="open",
    )

    session.add(incident)

    await session.commit()
    await session.refresh(incident)

    return incident


async def get_recent_incidents(
    session: AsyncSession,
    station_id: str,
    limit: int = 20,
) -> list[Incident]:
    result = await session.execute(
        select(Incident)
        .where(
            Incident.station_id
            == station_id.upper()
        )
        .order_by(
            Incident.created_at.desc()
        )
        .limit(limit)
    )

    return list(
        result.scalars().all()
    )


async def get_incident(
    session: AsyncSession,
    incident_id: int,
) -> Incident | None:
    result = await session.execute(
        select(Incident).where(
            Incident.id == incident_id
        )
    )

    return result.scalar_one_or_none()


async def update_incident_status(
    session: AsyncSession,
    incident_id: int,
    status: str,
) -> Incident | None:
    incident = await get_incident(
        session,
        incident_id,
    )

    if incident is None:
        return None

    incident.status = status

    await session.commit()
    await session.refresh(incident)

    return incident