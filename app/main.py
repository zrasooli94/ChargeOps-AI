import logging
from contextlib import asynccontextmanager

from fastapi import (
    Depends,
    FastAPI,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from app.api.agent import (
    router as agent_router,
)
from app.api.analysis import (
    router as analysis_router,
)
from app.api.auth import (
    router as auth_router,
)
from app.api.chat import (
    router as chat_router,
)
from app.api.incidents import (
    router as incidents_router,
)
from app.api.knowledge import (
    router as knowledge_router,
)
from app.api.observability import (
    router as observability_router,
)
from app.api.stations import (
    router as stations_router,
)
from app.api.users import (
    router as users_router,
)
from app.api.weather import (
    router as weather_router,
)
from app.core.auth_dependencies import (
    require_operator,
    require_viewer,
)
from app.core.checkpointing import (
    close_checkpointing,
    initialize_checkpointing,
)
from app.core.config import settings
from app.core.security_headers import (
    SecurityHeadersMiddleware,
)

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(name)s | "
        "%(levelname)s | %(message)s"
    ),
)


@asynccontextmanager
async def lifespan(
    _: FastAPI,
):
    await initialize_checkpointing()

    yield

    await close_checkpointing()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# =================================================
# CORS
# =================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings
        .cors_allowed_origins_list
    ),
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
    ],
)

# =================================================
# Security headers
# =================================================

app.add_middleware(
    SecurityHeadersMiddleware,
    enable_hsts=(
        settings
        .security_enable_hsts
    ),
    hsts_max_age=(
        settings
        .security_hsts_max_age
    ),
)

# =================================================
# Public / self-authenticated routes
# =================================================

app.include_router(
    auth_router
)

app.include_router(
    users_router
)

# =================================================
# Agent
#
# /agent/run    -> viewer+
# /agent/resume -> operator+
#
# These permissions are already enforced
# directly inside app/api/agent.py.
# =================================================

app.include_router(
    agent_router
)


# =================================================
# Viewer routes
# =================================================

app.include_router(
    chat_router,
    dependencies=[
        Depends(
            require_viewer
        ),
    ],
)

app.include_router(
    weather_router,
    dependencies=[
        Depends(
            require_viewer
        ),
    ],
)

app.include_router(
    stations_router,
    dependencies=[
        Depends(
            require_viewer
        ),
    ],
)


# =================================================
# Operator routes
# =================================================

app.include_router(
    analysis_router,
    dependencies=[
        Depends(
            require_operator
        ),
    ],
)

app.include_router(
    observability_router,
    dependencies=[
        Depends(
            require_operator
        ),
    ],
)


# =================================================
# Temporary conservative boundaries
#
# We refine these to per-endpoint RBAC next.
# =================================================

app.include_router(
    incidents_router
)

app.include_router(
    knowledge_router
)


# =================================================
# Public health endpoint
# =================================================

@app.get(
    "/health"
)
def health_check() -> dict[
    str,
    str,
]:
    return {
        "status": "ok",
        "app": settings.app_name,
    }