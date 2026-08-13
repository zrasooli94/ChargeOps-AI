import logging
import secrets
from time import perf_counter

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
)
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.responses import Response

from app.core.config import settings

logger = logging.getLogger(
    "chargeops.monitoring"
)


# =================================================
# Prometheus metrics
# =================================================


HTTP_REQUESTS_TOTAL = Counter(
    "chargeops_http_requests_total",
    "Total ChargeOps HTTP requests.",
    [
        "method",
        "route",
        "status_code",
    ],
)


HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "chargeops_http_request_duration_seconds",
    "ChargeOps HTTP request duration in seconds.",
    [
        "method",
        "route",
    ],
    buckets=(
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
    ),
)


HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "chargeops_http_requests_in_progress",
    "ChargeOps HTTP requests currently running.",
    [
        "method",
    ],
)


HTTP_EXCEPTIONS_TOTAL = Counter(
    "chargeops_http_exceptions_total",
    "Unhandled exceptions during ChargeOps HTTP requests.",
    [
        "method",
        "route",
    ],
)


# Render calls health endpoints frequently.
# They should not dominate application traffic metrics.
EXCLUDED_PATHS = {
    "/metrics",
    "/health/live",
    "/health/ready",
}


# =================================================
# Helpers
# =================================================


def _route_template(
    request: Request,
) -> str:
    route = request.scope.get(
        "route"
    )

    path = getattr(
        route,
        "path",
        None,
    )

    if isinstance(
        path,
        str,
    ):
        return path

    # Never fall back to the raw request path.
    # Dynamic IDs would create unbounded metric labels.
    return "unmatched"


def _metrics_access_allowed(
    authorization: str | None,
) -> bool:
    token = (
        settings.monitoring_metrics_token
    )

    if (
        settings.app_environment
        != "production"
    ):
        return True

    if not token:
        return False

    if not authorization:
        return False

    scheme, separator, supplied_token = (
        authorization.partition(" ")
    )

    if (
        separator != " "
        or scheme.lower() != "bearer"
    ):
        return False

    return secrets.compare_digest(
        supplied_token,
        token,
    )


# =================================================
# HTTP metrics middleware
# =================================================


class HTTPMetricsMiddleware(
    BaseHTTPMiddleware
):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if (
            request.url.path
            in EXCLUDED_PATHS
        ):
            return await call_next(
                request
            )

        method = request.method
        started_at = perf_counter()

        route_name = "unmatched"
        status_code = "500"

        HTTP_REQUESTS_IN_PROGRESS.labels(
            method=method
        ).inc()

        try:
            response = await call_next(
                request
            )

            status_code = str(
                response.status_code
            )

            route_name = (
                _route_template(
                    request
                )
            )

            return response

        except Exception:
            route_name = (
                _route_template(
                    request
                )
            )

            HTTP_EXCEPTIONS_TOTAL.labels(
                method=method,
                route=route_name,
            ).inc()

            raise

        finally:
            duration_seconds = (
                perf_counter()
                - started_at
            )

            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                route=route_name,
                status_code=status_code,
            ).inc()

            (
                HTTP_REQUEST_DURATION_SECONDS
                .labels(
                    method=method,
                    route=route_name,
                )
                .observe(
                    duration_seconds
                )
            )

            HTTP_REQUESTS_IN_PROGRESS.labels(
                method=method
            ).dec()

            render_request_id = (
                request.headers.get(
                    "rndr-id",
                    "-",
                )
            )

            cloudflare_ray = (
                request.headers.get(
                    "cf-ray",
                    "-",
                )
            )

            logger.info(
                (
                    "HTTP request completed "
                    "method=%s "
                    "route=%s "
                    "status=%s "
                    "duration_ms=%.2f "
                    "rndr_id=%s "
                    "cf_ray=%s"
                ),
                method,
                route_name,
                status_code,
                (
                    duration_seconds
                    * 1000
                ),
                render_request_id,
                cloudflare_ray,
            )


# =================================================
# Monitoring registration
# =================================================


def configure_monitoring(
    app: FastAPI,
) -> None:
    app.add_middleware(
        HTTPMetricsMiddleware
    )

    @app.get(
        "/metrics",
        include_in_schema=False,
    )
    async def prometheus_metrics(
        request: Request,
    ) -> Response:
        authorization = (
            request.headers.get(
                "authorization"
            )
        )

        if not _metrics_access_allowed(
            authorization
        ):
            raise HTTPException(
                status_code=401,
                detail=(
                    "Monitoring credentials "
                    "are required."
                ),
            )

        return Response(
            content=generate_latest(),
            media_type=(
                CONTENT_TYPE_LATEST
            ),
        )