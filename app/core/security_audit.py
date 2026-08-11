import hashlib
import json
import logging
from datetime import (
    datetime,
    timezone,
)
from typing import Literal
from uuid import UUID

logger = logging.getLogger(
    "chargeops.security"
)


SecurityOutcome = Literal[
    "success",
    "failure",
    "denied",
]

SecuritySeverity = Literal[
    "INFO",
    "WARNING",
    "ERROR",
]


def _safe_text(
    value: object,
    *,
    max_length: int = 250,
) -> str:
    text = str(
        value
    )

    text = (
        text
        .replace(
            "\r",
            "\\r",
        )
        .replace(
            "\n",
            "\\n",
        )
    )

    return text[
        :max_length
    ]


def fingerprint_identifier(
    value: str,
) -> str:
    """
    Create a stable fingerprint without storing
    the original email address in security logs.
    """

    normalized = (
        value
        .strip()
        .casefold()
        .encode(
            "utf-8"
        )
    )

    return (
        hashlib.sha256(
            normalized
        )
        .hexdigest()[:20]
    )


def log_security_event(
    *,
    event: str,
    outcome: SecurityOutcome,
    severity: SecuritySeverity = "INFO",
    user_id: (
        UUID
        | str
        | None
    ) = None,
    user_role: (
        str
        | None
    ) = None,
    client_ip: (
        str
        | None
    ) = None,
    email: (
        str
        | None
    ) = None,
    request_id: (
        str
        | None
    ) = None,
    target: (
        str
        | None
    ) = None,
    reason: (
        str
        | None
    ) = None,
) -> None:
    payload: dict[
        str,
        str,
    ] = {
        "timestamp": (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        ),
        "event": (
            _safe_text(
                event
            )
        ),
        "outcome": outcome,
    }

    if user_id is not None:
        payload[
            "user_id"
        ] = _safe_text(
            user_id
        )

    if user_role is not None:
        payload[
            "user_role"
        ] = _safe_text(
            user_role
        )

    if client_ip is not None:
        payload[
            "client_ip"
        ] = _safe_text(
            client_ip
        )

    if email is not None:
        payload[
            "email_fingerprint"
        ] = fingerprint_identifier(
            email
        )

    if request_id is not None:
        payload[
            "request_id"
        ] = _safe_text(
            request_id
        )

    if target is not None:
        payload[
            "target"
        ] = _safe_text(
            target
        )

    if reason is not None:
        payload[
            "reason"
        ] = _safe_text(
            reason
        )

    level = getattr(
        logging,
        severity,
    )

    logger.log(
        level,
        "security_event=%s",
        json.dumps(
            payload,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
        ),
    )