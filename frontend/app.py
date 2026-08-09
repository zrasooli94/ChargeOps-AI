import os

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv(
    "CHARGEOPS_API_URL",
    "http://127.0.0.1:8000",
)


st.set_page_config(
    page_title="ChargeOps AI",
    page_icon="⚡",
    layout="wide",
)


def check_backend() -> bool:
    try:
        response = httpx.get(
            f"{API_BASE_URL}/health",
            timeout=3.0,
        )

        return response.status_code == 200

    except httpx.HTTPError:
        return False


def run_agent(
    station_id: str,
    charger_model: str,
    latitude: float,
    longitude: float,
    message: str,
) -> dict:
    response = httpx.post(
        f"{API_BASE_URL}/agent/run",
        json={
            "station_id": station_id,
            "charger_model": charger_model,
            "latitude": latitude,
            "longitude": longitude,
            "message": message,
        },
        timeout=90.0,
    )

    response.raise_for_status()

    return response.json()


def show_tool_activity(
    tools: list[str],
    trace: list[dict],
) -> None:
    if not tools:
        st.caption(
            "💬 No external tools required"
        )
        return

    st.caption(
        "🔧 Tools used: "
        + ", ".join(tools)
    )

    with st.expander(
        "🔍 Agent Activity",
        expanded=True,
    ):
        for event in trace:
            tool_name = event.get(
                "tool",
                "unknown_tool",
            )

            summary = event.get(
                "summary",
                "Completed successfully",
            )

            st.success(
                f"{tool_name}: {summary}"
            )


st.title("⚡ ChargeOps AI")

st.caption(
    "Agentic EV Charging Intelligence "
    "& Operations Platform"
)


# -------------------------------------------------
# Sidebar
# -------------------------------------------------

with st.sidebar:
    st.header("Station Context")

    station_id = st.text_input(
        "Station ID",
        value="KL-205",
    )

    charger_model = st.text_input(
        "Charger Model",
        value="ABB Terra 54",
    )

    latitude = st.number_input(
        "Latitude",
        min_value=-90.0,
        max_value=90.0,
        value=3.139000,
        format="%.6f",
    )

    longitude = st.number_input(
        "Longitude",
        min_value=-180.0,
        max_value=180.0,
        value=101.686900,
        format="%.6f",
    )

    st.divider()

    if check_backend():
        st.success(
            "Backend connected"
        )

    else:
        st.error(
            "Backend unavailable"
        )


# -------------------------------------------------
# Tabs
# -------------------------------------------------

tab_agent, tab_system = st.tabs(
    [
        "🤖 AI Agent",
        "ℹ️ System",
    ]
)


# -------------------------------------------------
# Agent tab
# -------------------------------------------------

with tab_agent:
    st.subheader(
        "Ask ChargeOps"
    )

    st.write(
        "Ask operational questions about the "
        "selected charging station. "
        "The agent decides automatically whether "
        "external tools are required."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous conversation.
    for message in st.session_state.messages:
        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )

            if message["role"] == "assistant":
                show_tool_activity(
                    message.get(
                        "tools",
                        [],
                    ),
                    message.get(
                        "trace",
                        [],
                    ),
                )

    prompt = st.chat_input(
        "Ask about the charging station..."
    )

    if prompt:
        # Save user message.
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response.
        with st.chat_message("assistant"), st.spinner(
            "ChargeOps AI is analyzing..."
        ):
            try:
                result = run_agent(
                    station_id=station_id,
                    charger_model=charger_model,
                    latitude=latitude,
                    longitude=longitude,
                    message=prompt,
                )

                answer = result.get(
                    "answer",
                    "No response returned.",
                )

                tools = result.get(
                    "used_tools",
                    [],
                )

                trace = result.get(
                    "trace",
                    [],
                )

                st.markdown(answer)

                show_tool_activity(
                    tools,
                    trace,
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "tools": tools,
                        "trace": trace,
                    }
                )

            except httpx.HTTPStatusError as error:
                try:
                    error_data = (
                        error.response.json()
                    )

                    detail = error_data.get(
                        "detail",
                        "Unknown backend error",
                    )

                except ValueError:
                    detail = (
                        error.response.text
                    )

                st.error(
                    f"Backend error "
                    f"({error.response.status_code}): "
                    f"{detail}"
                )

            except httpx.HTTPError as error:
                st.error(
                    "Could not connect to the "
                    "ChargeOps backend."
                )

                st.caption(
                    str(error)
                )


# -------------------------------------------------
# System tab
# -------------------------------------------------

with tab_system:
    st.subheader(
        "Current Architecture"
    )

    st.code(
        """
User
  ↓
Streamlit
  ↓
FastAPI
  ↓
ChargeOps Agent
  ↓
OpenAI Tool Decision
  ├── Direct Answer
  ├── Weather Tool
  ├── Diagnostic Tool
  └── Multiple Tools
        """
    )

    st.subheader(
        "Agent Capabilities"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
### 🌦 Weather Tool

Retrieves real current weather data for
the selected charging station.

Used for questions involving:

- Temperature
- Rain
- Wind
- Weather-related charger issues
- Environmental operating conditions
            """
        )

    with col2:
        st.markdown(
            """
### 🔧 Diagnostic Tool

Performs structured analysis of EV
charging faults.

Used for:

- Overheating
- Network failures
- Hardware faults
- Power problems
- Payment issues
- Troubleshooting
            """
        )

    st.divider()

    st.subheader(
        "Current Project Features"
    )

    st.markdown(
        """
- FastAPI backend
- Streamlit frontend
- OpenAI Responses API
- Structured outputs
- Async LLM requests
- Multi-tool AI agent
- Automatic tool selection
- Real-time weather integration
- Structured EV fault diagnosis
- Agent activity trace
- Pydantic validation
- Error handling
- Automated testing
- Ruff code quality checks
        """
    )