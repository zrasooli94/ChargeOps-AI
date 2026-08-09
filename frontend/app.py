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


# =================================================
# Backend API functions
# =================================================


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


@st.cache_data(ttl=10)
def get_incidents(
    station_id: str,
) -> list[dict]:
    response = httpx.get(
        f"{API_BASE_URL}/incidents",
        params={
            "station_id": station_id,
            "limit": 100,
        },
        timeout=5.0,
    )

    response.raise_for_status()

    return response.json()


def update_incident_status(
    incident_id: int,
    status: str,
) -> dict:
    response = httpx.patch(
        f"{API_BASE_URL}/incidents/{incident_id}",
        json={
            "status": status,
        },
        timeout=5.0,
    )

    response.raise_for_status()

    return response.json()


def run_agent(
    station_id: str,
    message: str,
) -> dict:
    response = httpx.post(
        f"{API_BASE_URL}/agent/run",
        json={
            "station_id": station_id,
            "message": message,
        },
        timeout=90.0,
    )

    response.raise_for_status()

    return response.json()


# =================================================
# UI helper functions
# =================================================


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
                "Completed.",
            )

            status = event.get(
                "status",
                "success",
            )

            if status == "error":
                st.error(
                    f"{tool_name}: {summary}"
                )

            else:
                st.success(
                    f"{tool_name}: {summary}"
                )


def show_severity(
    severity: str,
) -> None:
    severity_lower = severity.lower()

    if severity_lower == "critical":
        st.error(
            "🔴 Critical"
        )

    elif severity_lower == "high":
        st.warning(
            "🟠 High"
        )

    elif severity_lower == "medium":
        st.info(
            "🟡 Medium"
        )

    else:
        st.success(
            "🟢 Low"
        )


# =================================================
# Main header
# =================================================


st.title(
    "⚡ ChargeOps AI"
)

st.caption(
    "Agentic EV Charging Intelligence "
    "& Operations Platform"
)


# =================================================
# Backend check
# =================================================


if not check_backend():
    st.error(
        "ChargeOps backend is unavailable."
    )

    st.info(
        "Start FastAPI with: "
        "`uvicorn app.main:app --reload`"
    )

    st.stop()


# =================================================
# Load stations
# =================================================


try:
    stations = get_stations()

except httpx.HTTPError as error:
    st.error(
        "Could not retrieve charging stations."
    )

    st.caption(
        str(error)
    )

    st.stop()


if not stations:
    st.warning(
        "No charging stations are available."
    )

    st.stop()


# =================================================
# Sidebar
# =================================================


with st.sidebar:
    st.header(
        "⚡ Station Context"
    )

    st.success(
        "Backend connected"
    )

    station_lookup = {
        (
            f"{station['station_id']} — "
            f"{station['name']}"
        ): station
        for station in stations
    }

    selected_station_label = st.selectbox(
        "Charging Station",
        options=list(
            station_lookup.keys()
        ),
    )

    selected_station = station_lookup[
        selected_station_label
    ]

    station_id = selected_station[
        "station_id"
    ]

    station_name = selected_station[
        "name"
    ]

    charger_model = selected_station[
        "charger_model"
    ]

    location = selected_station[
        "location"
    ]

    latitude = selected_station[
        "latitude"
    ]

    longitude = selected_station[
        "longitude"
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
        f"**Name:** {station_name}"
    )

    st.write(
        f"**Model:** {charger_model}"
    )

    st.write(
        f"**Location:** {location}"
    )

    st.caption(
        f"{latitude:.6f}, "
        f"{longitude:.6f}"
    )

    if station_status.lower() == "active":
        st.success(
            "● Active"
        )

    elif (
        station_status.lower()
        == "maintenance"
    ):
        st.warning(
            "● Maintenance"
        )

    else:
        st.info(
            f"● {station_status.title()}"
        )

    st.divider()

    if st.button(
        "🔄 Refresh Data",
        use_container_width=True,
    ):
        st.cache_data.clear()
        st.rerun()


# =================================================
# Load incidents for selected station
# =================================================


try:
    incidents = get_incidents(
        station_id
    )

except httpx.HTTPError:
    incidents = []


# =================================================
# Main operational metrics
# =================================================


total_incidents = len(
    incidents
)

open_incidents = sum(
    incident["status"] == "open"
    for incident in incidents
)

investigating_incidents = sum(
    incident["status"]
    == "investigating"
    for incident in incidents
)

resolved_incidents = sum(
    incident["status"]
    == "resolved"
    for incident in incidents
)


metric1, metric2, metric3, metric4 = (
    st.columns(4)
)

with metric1:
    st.metric(
        "Total Incidents",
        total_incidents,
    )

with metric2:
    st.metric(
        "Open",
        open_incidents,
    )

with metric3:
    st.metric(
        "Investigating",
        investigating_incidents,
    )

with metric4:
    st.metric(
        "Resolved",
        resolved_incidents,
    )


st.divider()


# =================================================
# Tabs
# =================================================


tab_agent, tab_incidents, tab_system = st.tabs(
    [
        "🤖 AI Agent",
        "📋 Incidents",
        "🏗 System",
    ]
)


# =================================================
# Agent tab
# =================================================


with tab_agent:
    st.subheader(
        "ChargeOps Operations Agent"
    )

    st.write(
        "Ask questions about the selected charging station, "
        "diagnose faults using the technical knowledge base, "
        "check current weather, or retrieve previous "
        "incident history."
    )

    st.info(
        f"Selected station: "
        f"**{station_id} — {station_name}**"
    )

    # ---------------------------------------------
    # Station-specific chat history
    # ---------------------------------------------

    if (
        "chat_histories"
        not in st.session_state
    ):
        st.session_state.chat_histories = {}

    if (
        station_id
        not in st.session_state.chat_histories
    ):
        st.session_state.chat_histories[
            station_id
        ] = []

    messages = (
        st.session_state.chat_histories[
            station_id
        ]
    )

    # ---------------------------------------------
    # Render chat
    # ---------------------------------------------

    for message in messages:
        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )

            if (
                message["role"]
                == "assistant"
            ):
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

    # ---------------------------------------------
    # Chat input
    # ---------------------------------------------

    prompt = st.chat_input(
        "Ask ChargeOps about this station..."
    )

    if prompt:
        messages.append(
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

                messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "tools": tools,
                        "trace": trace,
                    }
                )

                # A diagnosis may have created
                # a new incident.
                st.cache_data.clear()

            except (
                httpx.HTTPStatusError
            ) as error:
                try:
                    detail = (
                        error.response
                        .json()
                        .get(
                            "detail",
                            "Unknown error",
                        )
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
                    "Could not connect to "
                    "ChargeOps backend."
                )

                st.caption(
                    str(error)
                )


# =================================================
# Incidents tab
# =================================================


with tab_incidents:
    st.subheader(
        "Incident Management"
    )

    st.write(
        f"Operational incident history for "
        f"**{station_id} — {station_name}**."
    )

    if not incidents:
        st.info(
            "No incidents have been recorded "
            "for this station yet."
        )

    else:
        status_filter = st.selectbox(
            "Filter by status",
            [
                "All",
                "Open",
                "Investigating",
                "Resolved",
            ],
        )

        if status_filter == "All":
            filtered_incidents = incidents

        else:
            filtered_incidents = [
                incident
                for incident in incidents
                if incident["status"]
                == status_filter.lower()
            ]

        st.caption(
            f"Showing "
            f"{len(filtered_incidents)} "
            f"incident(s)"
        )

        for incident in filtered_incidents:
            incident_id = incident["id"]

            severity = incident[
                "severity"
            ]

            status = incident[
                "status"
            ]

            title = (
                f"Incident #{incident_id} — "
                f"{severity.upper()} — "
                f"{status.upper()}"
            )

            with st.expander(
                title,
                expanded=False,
            ):
                col1, col2, col3, col4 = (
                    st.columns(4)
                )

                with col1:
                    st.metric(
                        "Incident ID",
                        f"#{incident_id}",
                    )

                with col2:
                    st.metric(
                        "Category",
                        incident[
                            "category"
                        ].title(),
                    )

                with col3:
                    st.metric(
                        "Confidence",
                        (
                            f"{incident['confidence']:.0%}"
                        ),
                    )

                with col4:
                    st.metric(
                        "Status",
                        status.title(),
                    )

                show_severity(
                    severity
                )

                st.markdown(
                    "### Reported Issue"
                )

                st.write(
                    incident["issue"]
                )

                st.markdown(
                    "### AI Diagnostic Summary"
                )

                st.write(
                    incident["summary"]
                )

                st.markdown(
                    "### Likely Causes"
                )

                causes = incident.get(
                    "likely_causes",
                    [],
                )

                if causes:
                    for cause in causes:
                        st.write(
                            f"- {cause}"
                        )

                else:
                    st.caption(
                        "No likely causes recorded."
                    )

                st.markdown(
                    "### Diagnostic Steps"
                )

                steps = incident.get(
                    "diagnostic_steps",
                    [],
                )

                if steps:
                    for step in steps:
                        step_number = step.get(
                            "step",
                            "?",
                        )

                        action = step.get(
                            "action",
                            "",
                        )

                        st.write(
                            f"**{step_number}.** "
                            f"{action}"
                        )

                else:
                    st.caption(
                        "No diagnostic steps recorded."
                    )

                if incident.get(
                    "needs_human_escalation"
                ):
                    st.warning(
                        "⚠️ Human escalation recommended"
                    )

                created_at = incident.get(
                    "created_at"
                )

                if created_at:
                    st.caption(
                        f"Created: {created_at}"
                    )

                st.divider()

                st.markdown(
                    "### Incident Lifecycle"
                )

                valid_statuses = [
                    "open",
                    "investigating",
                    "resolved",
                ]

                current_index = (
                    valid_statuses.index(
                        status
                    )
                    if status
                    in valid_statuses
                    else 0
                )

                new_status = st.selectbox(
                    "Status",
                    valid_statuses,
                    index=current_index,
                    format_func=lambda value: (
                        value.title()
                    ),
                    key=(
                        f"incident_status_"
                        f"{incident_id}"
                    ),
                )

                if st.button(
                    "Update Status",
                    key=(
                        f"update_incident_"
                        f"{incident_id}"
                    ),
                ):
                    if (
                        new_status
                        == status
                    ):
                        st.info(
                            "Incident already has "
                            "this status."
                        )

                    else:
                        try:
                            update_incident_status(
                                incident_id=incident_id,
                                status=new_status,
                            )

                            st.success(
                                f"Incident "
                                f"#{incident_id} "
                                f"updated to "
                                f"{new_status.title()}."
                            )

                            st.cache_data.clear()

                            st.rerun()

                        except (
                            httpx.HTTPError
                        ) as error:
                            st.error(
                                "Could not update "
                                "incident status."
                            )

                            st.caption(
                                str(error)
                            )


# =================================================
# System tab
# =================================================


with tab_system:
    st.subheader(
        "ChargeOps Architecture"
    )

    st.code(
        """
User
  ↓
Streamlit Operations Dashboard
  │
  ├── Station Inventory
  │       ↓
  │    PostgreSQL
  │
  ├── Incident Management
  │       ↓
  │    PostgreSQL
  │
  └── ChargeOps Agent
            │
            ├── get_station_details
            │       ↓
            │    PostgreSQL
            │
            ├── get_recent_incidents
            │       ↓
            │    PostgreSQL
            │
            ├── get_station_weather
            │       ↓
            │    Weather API
            │
            ├── search_knowledge_base
            │       ↓
            │    OpenAI Embeddings
            │       ↓
            │    pgvector
            │
            └── diagnose_charging_issue
                    ↓
                 OpenAI
                    ↓
                Save Incident
        """
    )

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
        "Current Technology Stack"
    )

    stack1, stack2, stack3 = (
        st.columns(3)
    )

    with stack1:
        st.markdown(
            """
### AI

- OpenAI Responses API
- Structured Outputs
- Function Calling
- Multi-tool Agent
- Agent State
            """
        )

    with stack2:
        st.markdown(
            """
### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy Async
- PostgreSQL
            """
        )

    with stack3:
        st.markdown(
            """
### Platform

- Streamlit
- Docker
- Pytest
- Ruff
- Git / GitHub
            """
        )

    st.divider()

    st.subheader(
        "Agent Tools"
    )

    st.markdown(
        """
**1. `get_station_details`**  
Retrieves trusted station metadata from PostgreSQL.

**2. `get_recent_incidents`**  
Retrieves historical operational incidents.

**3. `get_station_weather`**  
Retrieves live external weather conditions.

**4. `search_knowledge_base`**  
Performs semantic retrieval over the EV charging technical knowledge base using embeddings and pgvector.

**5. `diagnose_charging_issue`**  
Performs structured fault analysis and automatically records incidents.




        """
    )