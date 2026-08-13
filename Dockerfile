FROM python:3.11-slim

# =================================================
# Python runtime configuration
# =================================================

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# =================================================
# uv / uvx
#
# ChargeOps needs uvx at runtime because the
# external MCP integration launches the Fetch MCP
# server through uvx.
# =================================================

COPY --from=ghcr.io/astral-sh/uv:0.11.32 \
    /uv \
    /uvx \
    /bin/

# =================================================
# Application user
# =================================================

RUN groupadd \
        --system \
        chargeops \
    && useradd \
        --system \
        --gid chargeops \
        --create-home \
        chargeops

# =================================================
# Working directory
# =================================================

WORKDIR /app

# =================================================
# Install Python dependencies separately so Docker
# can cache this expensive layer.
# =================================================

COPY requirements.txt .

RUN python -m pip install \
    --no-cache-dir \
    -r requirements.txt

# =================================================
# Copy application
# =================================================

COPY . .

# =================================================
# Writable runtime directories
# =================================================

RUN mkdir -p \
        /app/artifacts \
        /app/data/forecasting \
    && chown -R \
        chargeops:chargeops \
        /app

# =================================================
# Do not run the application as root
# =================================================

USER chargeops

# =================================================
# FastAPI default port
# =================================================

EXPOSE 8000

# =================================================
# Default service
#
# Compose will override this command for Streamlit,
# migrations, forecasting bootstrap and MCP.
# =================================================

# CMD ["sh", "-c", "python -m alembic upgrade head && python -m scripts.train_demand_forecast --generate-demo && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
CMD ["sh", "scripts/start_container.sh"]