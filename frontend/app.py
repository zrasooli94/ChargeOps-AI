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


# -------------------------------------------------
# Backend functions
# -------------------------------------------------


def check_backend() -> bool:
    try:
        response = httpx.get(
            f"{API_BASE_URL}/health",
            timeout=3.0,
        )

        return response.status_code == 200

    except httpx.HTTPError:
        return False


@st.cache_data(ttl=30)
def get_stations() -> list[dict]:
    response = httpx.get(
        f"{API_BASE_URL}/stations",
        timeout=5.0,
    )

    response.raise_for_status()

    return response.json()


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


# -------------------------------------------------
# UI helpers
# -------------------------------------------------


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


# -------------------------------------------------
# Header
# -------------------------------------------------


st.title("⚡ ChargeOps AI")

st.caption(
    "Agentic EV Charging Intelligence "
    "& Operations Platform"
)


# -------------------------------------------------
# Sidebar — database-driven station selection
# -------------------------------------------------


with st.sidebar:
    st.header("Station Context")

    backend_online = check_backend()

    if backend_online:
        st.success(
            "Backend connected"
        )

    else:
        st.error(
            "Backend unavailable"
        )

        st.stop()

    try:
        stations = get_stations()

    except httpx.HTTPStatusError as error:
        st.error(
            "Could not retrieve stations "
            f"({error.response.status_code})."
        )

        st.stop()

    except httpx.HTTPError:
        st.error(
            "Could not connect to the station database API."
        )

        st.stop()

    if not stations:
        st.warning(
            "No charging stations are available."
        )

        st.stop()

    station_lookup = {
        (
            f"{station['station_id']} — "
            f"{station['name']}"
        ): station
        for station in stations
    }

    selected_station_label = st.selectbox(
        "Charging Station",
        options=list(station_lookup.keys()),
    )

    selected_station = station_lookup[
        selected_station_label
    ]

    station_id = selected_station[
        "station_id"
    ]

    charger_model = selected_station[
        "charger_model"
    ]

    latitude = selected_station[
        "latitude"
    ]

    longitude = selected_station[
        "longitude"
    ]

    location = selected_station[
        "location"
    ]

    station_status = selected_station[
        "status"
    ]

    st.divider()

    st.subheader(
        "Station Details"
    )

    st.write(
        f"**ID:** {station_id}"
    )

    st.write(
        f"**Model:** {charger_model}"
    )

    st.write(
        f"**Location:** {location}"
    )

    st.write(
        f"**Latitude:** {latitude:.6f}"
    )

    st.write(
        f"**Longitude:** {longitude:.6f}"
    )

    if station_status.lower() == "active":
        st.success(
            "Status: Active"
        )

    elif station_status.lower() == "maintenance":
        st.warning(
            "Status: Maintenance"
        )

    else:
        st.info(
            f"Status: {station_status.title()}"
        )

    st.divider()

    if st.button(
        "🔄 Refresh Stations"
    ):
        st.cache_data.clear()
        st.rerun()


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

    st.info(
        f"Currently analyzing: "
        f"{station_id} — {selected_station['name']}"
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

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
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message(
            "user"
        ):
            st.markdown(
                prompt
            )

        with st.chat_message(
            "assistant"
        ), st.spinner(
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

                st.markdown(
                    answer
                )

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
  │
  ├── GET /stations
  │       ↓
  │    PostgreSQL
  │
  └── POST /agent/run
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
        "Data Layer"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Stations",
            len(stations),
        )

    with col2:
        active_count = sum(
            station["status"].lower()
            == "active"
            for station in stations
        )

        st.metric(
            "Active",
            active_count,
        )

    with col3:
        maintenance_count = sum(
            station["status"].lower()
            == "maintenance"
            for station in stations
        )

        st.metric(
            "Maintenance",
            maintenance_count,
        )

    st.divider()

    st.subheader(
        "Station Inventory"
    )

    st.dataframe(
        stations,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

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

Used for:

- Temperature
- Rain
- Wind
- Environmental conditions
- Weather-related charger issues
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
- PostgreSQL database
- Dockerized PostgreSQL
- Async SQLAlchemy
- OpenAI Responses API
- Structured AI outputs
- Multi-tool agent
- Automatic tool selection
- Real-time weather integration
- Structured EV fault diagnosis
- Agent activity trace
- Database-driven station selection
- Pydantic validation
- Error handling
- Automated testing
- Ruff code quality checks
        """
    )