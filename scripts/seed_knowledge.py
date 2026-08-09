import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.knowledge import KnowledgeChunk
from app.services.embedding_service import (
    create_embedding,
)

KNOWLEDGE = [
    {
        "document_key": "ocpp-connectivity-001",
        "title": "OCPP Connectivity Troubleshooting",
        "category": "network",
        "source": "ChargeOps Demo Knowledge Base",
        "content": (
            "When an EV charger repeatedly loses its OCPP connection, "
            "operators should check internet connectivity, DNS resolution, "
            "firewall rules, WebSocket connectivity, backend availability, "
            "TLS certificate validity, and charger network stability. "
            "Intermittent connectivity can cause repeated reconnect cycles "
            "even when the charging hardware itself is operating normally."
        ),
    },
    {
        "document_key": "thermal-management-001",
        "title": "Charger Over-Temperature Troubleshooting",
        "category": "hardware",
        "source": "ChargeOps Demo Knowledge Base",
        "content": (
            "Repeated over-temperature warnings may indicate blocked "
            "airflow, failed cooling fans, dirty filters, degraded thermal "
            "sensors, high internal resistance, poor connector contact, "
            "or excessive ambient heat. Operators should inspect the "
            "cooling system and connector temperature before repeatedly "
            "resetting the charger."
        ),
    },
    {
        "document_key": "power-input-001",
        "title": "EV Charger Input Power Faults",
        "category": "power",
        "source": "ChargeOps Demo Knowledge Base",
        "content": (
            "Input power faults can result from undervoltage, overvoltage, "
            "phase imbalance, loose electrical connections, upstream breaker "
            "problems, grounding faults, or unstable utility supply. "
            "Technicians should verify supply voltage and electrical "
            "connections before replacing charger electronics."
        ),
    },
    {
        "document_key": "connector-heating-001",
        "title": "Charging Connector Heating",
        "category": "hardware",
        "source": "ChargeOps Demo Knowledge Base",
        "content": (
            "Abnormal charging connector heating can be caused by worn "
            "contacts, contamination, loose connections, cable damage, "
            "high contact resistance, or inadequate cooling. Continued "
            "operation with excessive connector temperature can damage "
            "equipment and should be investigated promptly."
        ),
    },
    {
        "document_key": "payment-terminal-001",
        "title": "Charging Payment Failures",
        "category": "payment",
        "source": "ChargeOps Demo Knowledge Base",
        "content": (
            "Payment failures may originate from terminal connectivity, "
            "payment gateway outages, expired credentials, network latency, "
            "incorrect charger configuration, or backend authorization "
            "errors. Operators should separate payment-system faults from "
            "charging-hardware faults during troubleshooting."
        ),
    },
    {
        "document_key": "charger-offline-001",
        "title": "Offline EV Charging Station",
        "category": "network",
        "source": "ChargeOps Demo Knowledge Base",
        "content": (
            "An offline charging station should be checked for local power, "
            "router or modem status, cellular signal quality, Ethernet "
            "connectivity, firewall changes, backend reachability, and "
            "charger software health. A station can remain powered locally "
            "while appearing offline to the central management system."
        ),
    },
    {
        "document_key": "safe-reset-001",
        "title": "Safe Charger Reset Procedure",
        "category": "operations",
        "source": "ChargeOps Demo Knowledge Base",
        "content": (
            "Repeatedly resetting a charger without diagnosing the root "
            "cause can temporarily hide recurring faults. Operators should "
            "record error codes, review recent incidents, inspect relevant "
            "hardware and network conditions, and perform a controlled reset "
            "only after basic safety checks."
        ),
    },
    {
        "document_key": "weather-impact-001",
        "title": "Environmental Effects on EV Chargers",
        "category": "environment",
        "source": "ChargeOps Demo Knowledge Base",
        "content": (
            "High ambient temperature can reduce cooling margin and may "
            "contribute to thermal derating or overheating, especially when "
            "cooling components are degraded. Heavy rain and humidity can "
            "also expose enclosure sealing or insulation problems. Weather "
            "should be treated as contributing evidence rather than assumed "
            "to be the root cause of every charger fault."
        ),
    },
]


async def main() -> None:
    async with AsyncSessionLocal() as session:
        added = 0

        for item in KNOWLEDGE:
            existing_result = await session.execute(
                select(
                    KnowledgeChunk
                ).where(
                    KnowledgeChunk.document_key
                    == item["document_key"]
                )
            )

            existing = (
                existing_result.scalar_one_or_none()
            )

            if existing is not None:
                continue

            embedding = await create_embedding(
                item["content"]
            )

            chunk = KnowledgeChunk(
                document_key=item[
                    "document_key"
                ],
                title=item["title"],
                category=item["category"],
                source=item["source"],
                content=item["content"],
                embedding=embedding,
            )

            session.add(
                chunk
            )

            added += 1

        await session.commit()

    print(
        f"Knowledge base seeded: "
        f"{added} new chunk(s)."
    )


if __name__ == "__main__":
    asyncio.run(main())