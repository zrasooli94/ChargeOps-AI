#!/bin/sh

set -eu

SERVICE="${CHARGEOPS_SERVICE:-api}"

echo "Starting ChargeOps service: ${SERVICE}"

case "${SERVICE}" in
    api)
        echo "Applying database migrations..."
        python -m alembic upgrade head

        echo "Preparing forecasting model..."
        python -m scripts.train_demand_forecast \
            --generate-demo

        echo "Starting FastAPI..."
        exec uvicorn \
            app.main:app \
            --host 0.0.0.0 \
            --port "${PORT:-8000}"
        ;;

    frontend)
        echo "Starting Streamlit..."
        exec streamlit run \
            frontend/app.py \
            --server.address=0.0.0.0 \
            --server.port="${PORT:-8501}" \
            --server.headless=true \
            --server.baseUrlPath=""
        ;;

    *)
        echo "Unknown CHARGEOPS_SERVICE: ${SERVICE}"
        exit 64
        ;;
esac