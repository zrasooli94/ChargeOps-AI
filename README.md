# ChargeOps AI

ChargeOps AI is a production-style Generative AI and Agentic AI platform for EV charging operations. It combines a FastAPI backend, LangGraph-based agent orchestration, PostgreSQL/pgvector retrieval, human-in-the-loop operational controls, evaluation and observability, authentication/RBAC, and a Streamlit operations dashboard.

> Current development status: **Stage 13 — Authentication + RBAC complete. Stage 14 — Security Hardening next.**

## Why ChargeOps AI

The project is designed as a serious portfolio-grade AI engineering system rather than a simple chatbot. It demonstrates how an LLM can safely work with trusted operational data, external tools, retrieval-augmented generation, persistent memory, approval workflows, evaluation, observability, and deterministic authorization.

## Current Features

### Generative AI and Agentic AI

- OpenAI Responses API integration
- Configurable OpenAI model through environment variables
- Async LLM requests
- Structured outputs with Pydantic
- Deterministic escalation guardrails
- LangGraph StateGraph orchestration
- Multi-tool agent workflow
- Runtime context for trusted application state
- Persistent thread-scoped conversation memory
- PostgreSQL LangGraph checkpointing
- Human-in-the-loop approval for protected station-status changes
- Agent tool traces and execution metadata

### Agent Tools

The ChargeOps agent currently supports:

1. `get_station_details`
   - Retrieves trusted EV charging station metadata from PostgreSQL.

2. `get_recent_incidents`
   - Retrieves previous operational incidents for the selected station.

3. `get_station_weather`
   - Retrieves current weather conditions through an external weather API.

4. `search_knowledge_base`
   - Performs semantic retrieval across ChargeOps technical knowledge using embeddings and pgvector.

5. `diagnose_charging_issue`
   - Performs structured charging-fault diagnosis and records a successful diagnosis as an operational incident.
   - Restricted to operator/admin workflows.

6. `change_station_status`
   - Requests an operational station-status change.
   - Requires explicit human approval before execution.
   - Restricted to operator/admin workflows.

## Retrieval-Augmented Generation

- PostgreSQL with pgvector
- OpenAI `text-embedding-3-small`
- 1536-dimensional vectors
- HNSW cosine-similarity indexing
- Semantic knowledge search
- Retrieval similarity thresholds
- Result deduplication and diversity controls
- Source labels / citations
- RAG evidence returned through the agent response contract

### Document Ingestion

ChargeOps can ingest technical documents into the knowledge base:

- PDF
- TXT
- Markdown

The ingestion pipeline includes:

```text
Upload
  ↓
Validation
  ↓
Text extraction
  ↓
Normalization
  ↓
Chunking
  ↓
Embedding generation
  ↓
PostgreSQL + pgvector
  ↓
Semantic retrieval
```

Additional protections include:

- 10 MB upload limit
- Duplicate-document detection
- SHA-based document identification
- Rejection of unsupported/encrypted/scanned PDFs when text cannot be extracted
- Document listing and deletion
- Admin-only knowledge upload/delete operations

## EV Charging Operations Data

ChargeOps stores trusted operational data in PostgreSQL.

### Stations

Station records include information such as:

- Station ID
- Name
- Charger model
- Location
- Latitude / longitude
- Operational status

### Incidents

Operational incidents include:

- Issue description
- Diagnostic category
- Severity
- Confidence
- Likely causes
- Diagnostic steps
- Human-escalation recommendation
- Lifecycle status:
  - `open`
  - `investigating`
  - `resolved`

Incident history is readable by authenticated users, while incident-status modification requires operator or admin permission.

## Authentication and RBAC

ChargeOps implements deterministic server-side authentication and role-based access control.

### Authentication

- PostgreSQL-backed users
- Argon2 password hashing through `pwdlib`
- JWT access tokens
- Configurable token expiration
- `/auth/login`
- `/auth/me`
- Active-account validation
- Current database user loaded on authenticated requests
- Database role is authoritative even if an older JWT contains a previous role

### Roles

ChargeOps currently supports:

| Capability | Viewer | Operator | Admin |
|---|:---:|:---:|:---:|
| View stations | ✅ | ✅ | ✅ |
| View incidents | ✅ | ✅ | ✅ |
| Search knowledge | ✅ | ✅ | ✅ |
| View indexed documents | ✅ | ✅ | ✅ |
| Safe agent queries | ✅ | ✅ | ✅ |
| Update incident status | ❌ | ✅ | ✅ |
| Run operational diagnosis/write tools | ❌ | ✅ | ✅ |
| Resume protected HITL operations | ❌ | ✅ | ✅ |
| View observability | ❌ | ✅ | ✅ |
| Run direct analysis endpoint | ❌ | ✅ | ✅ |
| Upload knowledge documents | ❌ | ❌ | ✅ |
| Delete knowledge documents | ❌ | ❌ | ✅ |
| Manage users | ❌ | ❌ | ✅ |

### Admin User Management

Admins can:

- List ChargeOps users
- Create viewer/operator/admin accounts
- Change user roles
- Activate accounts
- Deactivate accounts

Additional protections:

- No public user registration
- Password hashes are never returned by API responses
- Admins cannot remove their own admin role
- Admins cannot deactivate their own account
- Role/account-state changes take effect on subsequent authenticated requests

## Human-in-the-Loop Safety

Protected station-status changes are not executed immediately by the LLM.

```text
User request
  ↓
Agent identifies protected action
  ↓
Authorization check
  ↓
LangGraph interrupt
  ↓
Human approval required
  ↓
Approve / Reject
  ↓
Resume workflow
  ↓
Database write only if approved and authorized
```

The LLM cannot grant itself permission. Authorization is enforced deterministically by application code.

## Observability

ChargeOps stores agent execution telemetry in PostgreSQL and integrates with LangSmith.

Tracked information includes:

- Run ID
- Thread ID
- Station ID
- User request
- Model
- Used tools
- Execution trace
- Latency
- Status
- Human-approval requirement
- Approval decision
- Final answer

The Streamlit dashboard includes recent-run metrics and a run inspector.

## Evaluation

ChargeOps includes repeatable evaluation workflows.

### Deterministic Agent Evaluation

Checks behaviors such as:

- Correct tool selection
- Required tool ordering
- Station context handling
- Protected-action behavior
- Incident creation expectations

### LangSmith Evaluation

ChargeOps has been evaluated using LangSmith datasets and experiments for:

- Deterministic agent behavior
- Semantic answer quality
- RAG groundedness
- Retrieval relevance
- Citation validity
- Citation faithfulness

Evaluation scripts are stored under:

```text
scripts/
```

and evaluation datasets/configuration under:

```text
evals/
```

## Streamlit Operations Dashboard

The frontend provides an authenticated operations interface.

Features include:

- Login/logout
- JWT session handling
- Automatic Bearer-token API requests
- Session-expiration handling
- Role-aware UI controls
- Station selection and station context
- Agent conversations
- Per-station thread IDs
- Conversation reset
- Human approval / rejection workflow
- Incident management
- Knowledge-base search
- Admin-only knowledge ingestion/deletion
- Operator/admin observability
- Admin-only user management
- System architecture overview

The frontend intentionally hides controls that a role cannot use, while FastAPI remains the authoritative security boundary.

## Architecture

```text
                         ┌──────────────────────┐
                         │      Streamlit       │
                         │ Operations Dashboard │
                         └──────────┬───────────┘
                                    │
                                    │ JWT Bearer Token
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │ Auth + RBAC + APIs   │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼───────────────────────┐
             │                      │                       │
             ▼                      ▼                       ▼
    ┌────────────────┐    ┌──────────────────┐    ┌──────────────────┐
    │   LangGraph    │    │    PostgreSQL    │    │ External Services│
    │ ChargeOps Agent│    │ + pgvector       │    │ Weather / OpenAI │
    └───────┬────────┘    └─────────┬────────┘    └──────────────────┘
            │                       │
            │                       ├── Stations
            │                       ├── Incidents
            │                       ├── Users
            │                       ├── Knowledge
            │                       ├── Agent Runs
            │                       └── Checkpoints
            │
            ├── Station Details
            ├── Incident History
            ├── Weather
            ├── RAG Search
            ├── Diagnosis
            └── Protected Status Change
                        │
                        ▼
                Human-in-the-Loop
                  Approval Gate
```

## Project Structure

```text
ChargeOps-AI/
├── alembic/
│   ├── env.py
│   └── versions/
├── app/
│   ├── agents/
│   │   └── chargeops_graph.py
│   ├── api/
│   │   ├── agent.py
│   │   ├── analysis.py
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── incidents.py
│   │   ├── knowledge.py
│   │   ├── observability.py
│   │   ├── stations.py
│   │   ├── users.py
│   │   └── weather.py
│   ├── core/
│   │   ├── auth_dependencies.py
│   │   ├── checkpointing.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── openai_client.py
│   │   └── security.py
│   ├── models/
│   │   ├── agent_run.py
│   │   ├── incident.py
│   │   ├── knowledge.py
│   │   ├── station.py
│   │   └── user.py
│   ├── schemas/
│   ├── services/
│   └── main.py
├── evals/
├── frontend/
│   └── app.py
├── scripts/
├── tests/
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md
```

## Technology Stack

### AI

- OpenAI Responses API
- Structured Outputs
- Function Calling
- LangGraph
- RAG
- OpenAI Embeddings
- LangSmith
- LLM-as-judge evaluation

### Backend

- Python 3.11
- FastAPI
- Pydantic
- SQLAlchemy Async
- Alembic
- PyJWT
- pwdlib / Argon2

### Data

- PostgreSQL
- pgvector
- HNSW vector indexing

### Frontend

- Streamlit
- httpx

### Engineering

- Pytest
- Ruff
- Docker / Docker Compose
- Git / GitHub

## Local Development

### 1. Create and activate a virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example configuration and provide local secrets:

```bash
cp .env.example .env
```

Never commit `.env` or real API/JWT secrets.

### 4. Start PostgreSQL

```bash
docker compose up -d
docker compose ps
```

### 5. Apply database migrations

```bash
python -m alembic upgrade head
```

### 6. Start FastAPI

```bash
uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### 7. Start Streamlit

In another terminal:

```bash
streamlit run frontend/app.py
```

Streamlit:

```text
http://localhost:8501
```

## Quality Checks

Run Ruff:

```bash
python -m ruff check .
```

Run the full test suite:

```bash
python -m pytest -q
```

Check migrations:

```bash
python -m alembic current
```

## Security Principles

ChargeOps follows these design principles:

- Authentication and authorization are enforced server-side.
- LLM prompts never determine access control.
- Database user role/account state is checked on authenticated requests.
- Protected operational writes require both authorization and human approval.
- Secrets remain in environment variables and are excluded from version control.
- Password hashes are never exposed by API responses.
- Knowledge-base writes are admin-only.
- UI role restrictions improve usability but never replace backend authorization.

## Development Roadmap

Completed major stages include:

- Software + AI foundation
- Structured GenAI
- External integrations
- PostgreSQL operational intelligence
- RAG
- Production knowledge ingestion
- Agentic AI
- LangGraph orchestration
- Persistent agent memory
- Human-in-the-loop workflows
- Observability
- Evaluation engineering
- Authentication + RBAC

### Next

**Stage 14 — Security Hardening**

Planned work includes:

- Login rate limiting / brute-force protection
- Authentication timing protection
- Stronger password policy
- CORS hardening
- Security headers
- JWT/session hardening
- Secret-management cleanup
- Security-sensitive audit logging
- Safer production error handling
- Security regression tests

## License

A project license has not yet been selected.
