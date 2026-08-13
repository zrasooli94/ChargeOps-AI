# ChargeOps AI — Demo Guide

ChargeOps AI is an Agentic EV Charging Intelligence & Operations Platform.

## Live Application

Frontend:

https://chargeops-frontend.onrender.com

API documentation:

https://chargeops-api.onrender.com/docs

## Recommended Demo Flow

### 1. Station Intelligence

Select a charging station and inspect its operational status and metadata.

### 2. Agentic AI

Ask:

> What is the current status of this station and what operational issues should I investigate?

The ChargeOps agent can select and execute tools based on the request.

### 3. Live Weather

Ask:

> Check the current weather for this station and explain whether it could affect charging operations.

### 4. Demand Forecasting

Open Demand Forecast and generate a 24-hour charging-demand forecast.

The forecasting subsystem combines temporal, weather, station and historical-demand features.

### 5. Retrieval-Augmented Generation

Ask:

> According to the technical knowledge base, what should I check when an OCPP charger repeatedly loses connectivity?

The agent retrieves relevant technical knowledge using embeddings and PostgreSQL/pgvector.

### 6. Human-in-the-Loop

Operational changes can require explicit human approval before execution.

### 7. Observability

Inspect Agent Runs to review:

- model execution
- tool use
- latency
- execution traces
- conversation threads
- results

## Architecture Highlights

ChargeOps combines:

- FastAPI
- Streamlit
- OpenAI APIs
- LangGraph
- PostgreSQL
- pgvector
- RAG
- MCP
- machine-learning demand forecasting
- authentication and RBAC
- human-in-the-loop operations
- LangSmith observability
- Prometheus-compatible metrics
- Docker
- GitHub Actions CI/CD
- Render cloud deployment

## Important Demo Note

The forecasting dataset currently uses simulated demonstration demand history to validate the forecasting and operational-intelligence pipeline.

It should not be interpreted as production utility telemetry.