# ChargeOps AI

ChargeOps AI is an AI-powered EV charging operations platform being developed as a production-style Generative AI and Agentic AI project.

## Current Features

- FastAPI backend
- OpenAI Responses API integration
- Async LLM requests
- Pydantic request validation
- Environment-based configuration
- LLM error handling
- Application logging
- Automated API tests
- Ruff code quality checks

## Project Structure

```text
app/
├── api/
│   └── chat.py
├── core/
│   └── config.py
├── schemas/
│   └── chat.py
├── services/
│   └── llm_service.py
└── main.py

tests/
└── test_health.py


## Streamlit Frontend

ChargeOps AI includes an interactive Streamlit interface for interacting with the tool-calling agent.

Start the FastAPI backend:

```bash
uvicorn app.main:app --reload

**Current Features**
```markdown
- Streamlit interactive frontend
- Tool-calling AI agent
- Real-time weather tool
- Automatic tool selection

