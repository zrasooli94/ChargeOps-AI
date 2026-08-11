import os
from uuid import uuid4

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


def clear_auth_session() -> None:
    keys_to_clear = (
        "access_token",
        "current_user",
        "agent_thread_ids",
        "pending_approvals",
        "chat_histories",
    )

    for key in keys_to_clear:
        st.session_state.pop(
            key,
            None,
        )


def login_user(
    email: str,
    password: str,
) -> str:
    response = httpx.post(
        f"{API_BASE_URL}/auth/login",
        data={
            "username": email,
            "password": password,
        },
        timeout=10.0,
    )

    response.raise_for_status()

    payload = response.json()

    return str(
        payload["access_token"]
    )


def get_current_user(
    access_token: str,
) -> dict:
    response = httpx.get(
        f"{API_BASE_URL}/auth/me",
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            ),
        },
        timeout=10.0,
    )

    response.raise_for_status()

    return response.json()


def authenticated_request(
    method: str,
    path: str,
    access_token: str,
    timeout: float,
    **kwargs,
) -> httpx.Response:
    headers = dict(
        kwargs.pop(
            "headers",
            {},
        )
    )

    headers["Authorization"] = (
        f"Bearer {access_token}"
    )

    response = httpx.request(
        method=method,
        url=f"{API_BASE_URL}{path}",
        headers=headers,
        timeout=timeout,
        **kwargs,
    )

    if response.status_code == 401:
        clear_auth_session()
        st.cache_data.clear()

        st.warning(
            "Your ChargeOps session expired. "
            "Please sign in again."
        )

        st.rerun()

    response.raise_for_status()

    return response


@st.cache_data(
    ttl=10
)
def get_agent_runs(
    access_token: str,
    station_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    params: dict[
        str,
        str | int,
    ] = {
        "limit": limit,
    }

    if station_id:
        params[
            "station_id"
        ] = station_id

    response = authenticated_request(
        method="GET",
        path="/observability/runs",
        access_token=access_token,
        params=params,
        timeout=10.0,
    )

    return response.json()


@st.cache_data(ttl=30)
def get_stations(
    access_token: str,
) -> list[dict]:
    response = authenticated_request(
        method="GET",
        path="/stations",
        access_token=access_token,
        timeout=5.0,
    )

    return response.json()


@st.cache_data(ttl=10)
def get_incidents(
    access_token: str,
    station_id: str,
) -> list[dict]:
    response = authenticated_request(
        method="GET",
        path="/incidents",
        access_token=access_token,
        params={
            "station_id": station_id,
            "limit": 100,
        },
        timeout=5.0,
    )

    return response.json()


def run_agent(
    access_token: str,
    station_id: str,
    message: str,
    thread_id: str,
) -> dict:
    response = authenticated_request(
        method="POST",
        path="/agent/run",
        access_token=access_token,
        json={
            "station_id": station_id,
            "message": message,
            "thread_id": thread_id,
        },
        timeout=90.0,
    )

    return response.json()


def resume_agent(
    access_token: str,
    thread_id: str,
    approved: bool,
) -> dict:
    response = authenticated_request(
        method="POST",
        path="/agent/resume",
        access_token=access_token,
        json={
            "thread_id": thread_id,
            "approved": approved,
        },
        timeout=90.0,
    )

    return response.json()


@st.cache_data(ttl=15)
def get_knowledge_documents(
    access_token: str,
) -> list[dict]:
    response = authenticated_request(
        method="GET",
        path="/knowledge/documents",
        access_token=access_token,
        timeout=10.0,
    )

    return response.json()


def update_incident_status(
    access_token: str,
    incident_id: int,
    status: str,
) -> dict:
    response = authenticated_request(
        method="PATCH",
        path=(
            f"/incidents/{incident_id}"
        ),
        access_token=access_token,
        json={
            "status": status,
        },
        timeout=5.0,
    )

    return response.json()


def upload_knowledge_document(
    access_token: str,
    file_name: str,
    file_type: str,
    file_content: bytes,
    title: str,
    category: str,
) -> dict:
    response = authenticated_request(
        method="POST",
        path=(
            "/knowledge/documents/upload"
        ),
        access_token=access_token,
        files={
            "file": (
                file_name,
                file_content,
                file_type,
            ),
        },
        data={
            "title": title,
            "category": category,
        },
        timeout=120.0,
    )

    return response.json()


def delete_knowledge_document(
    access_token: str,
    document_id: int,
) -> None:
    authenticated_request(
        method="DELETE",
        path=(
            "/knowledge/documents/"
            f"{document_id}"
        ),
        access_token=access_token,
        timeout=10.0,
    )


def search_knowledge(
    access_token: str,
    query: str,
    limit: int,
) -> dict:
    response = authenticated_request(
        method="POST",
        path="/knowledge/search",
        access_token=access_token,
        json={
            "query": query,
            "limit": limit,
        },
        timeout=60.0,
    )

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


def show_http_error(
    error: httpx.HTTPStatusError,
) -> None:
    try:
        payload = error.response.json()

        detail = payload.get(
            "detail",
            "Unknown backend error",
        )

    except ValueError:
        detail = error.response.text

    st.error(
        f"Backend error "
        f"({error.response.status_code}): "
        f"{detail}"
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
# Backend health
# =================================================


if not check_backend():
    st.error(
        "ChargeOps backend is unavailable."
    )

    st.info(
        "Start FastAPI with "
        "`uvicorn app.main:app --reload`"
    )

    st.stop()


# =================================================
# Authentication
# =================================================


access_token = st.session_state.get(
    "access_token"
)

if not access_token:
    st.subheader(
        "🔐 Sign in to ChargeOps"
    )

    st.write(
        "Use your ChargeOps account to access "
        "the operations dashboard."
    )

    with st.form(
        "chargeops_login_form"
    ):
        email = st.text_input(
            "Email",
            placeholder=(
                "operator@chargeops.local"
            ),
        )

        password = st.text_input(
            "Password",
            type="password",
        )

        login_submitted = (
            st.form_submit_button(
                "Sign in",
                use_container_width=True,
            )
        )

    if login_submitted:
        if not email.strip() or not password:
            st.warning(
                "Enter your email and password."
            )

        else:
            try:
                token = login_user(
                    email=email.strip(),
                    password=password,
                )

                user = get_current_user(
                    token
                )

                st.session_state[
                    "access_token"
                ] = token

                st.session_state[
                    "current_user"
                ] = user

                st.cache_data.clear()
                st.rerun()

            except (
                httpx.HTTPStatusError
            ) as error:
                if (
                    error.response.status_code
                    == 401
                ):
                    st.error(
                        "Incorrect email or password."
                    )

                else:
                    show_http_error(
                        error
                    )

            except httpx.HTTPError as error:
                st.error(
                    "Could not connect to the "
                    "ChargeOps authentication service."
                )

                st.caption(
                    str(error)
                )

    st.stop()


try:
    current_user = get_current_user(
        access_token
    )

    st.session_state[
        "current_user"
    ] = current_user

except httpx.HTTPStatusError as error:
    if error.response.status_code == 401:
        clear_auth_session()
        st.cache_data.clear()

        st.warning(
            "Your ChargeOps session expired. "
            "Please sign in again."
        )

        st.rerun()

    show_http_error(
        error
    )
    st.stop()

except httpx.HTTPError as error:
    st.error(
        "Could not validate your ChargeOps session."
    )

    st.caption(
        str(error)
    )

    st.stop()


user_role = str(
    current_user.get(
        "role",
        "viewer",
    )
)

is_operator = user_role in {
    "operator",
    "admin",
}

is_admin = user_role == "admin"


# =================================================
# Load stations
# =================================================


try:
    stations = get_stations(
        access_token
    )

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
        "👤 Signed In"
    )

    st.write(
        current_user.get(
            "email",
            "Unknown user",
        )
    )

    st.caption(
        f"Role: {user_role.title()}"
    )

    if st.button(
        "🚪 Log out",
        use_container_width=True,
    ):
        clear_auth_session()
        st.cache_data.clear()
        st.rerun()

    st.divider()

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
# Load operational data
# =================================================


try:
    incidents = get_incidents(
        access_token,
        station_id,
    )

except httpx.HTTPError:
    incidents = []


try:
    knowledge_documents = (
        get_knowledge_documents(
            access_token
        )
    )

except httpx.HTTPError:
    knowledge_documents = []


# =================================================
# Top metrics
# =================================================


total_incidents = len(
    incidents
)

open_incidents = sum(
    incident["status"] == "open"
    for incident in incidents
)

investigating_incidents = sum(
    incident["status"] == "investigating"
    for incident in incidents
)

resolved_incidents = sum(
    incident["status"] == "resolved"
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
# Main tabs
# =================================================


(
    tab_agent,
    tab_incidents,
    tab_knowledge,
    tab_observability,
    tab_system,
) = st.tabs(
    [
        "🤖 Agent",
        "🚨 Incidents",
        "📚 Knowledge Base",
        "📊 Observability",
        "⚙️ System",
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
        "Ask questions about the selected charging "
        "station, diagnose faults using the technical "
        "knowledge base, check current weather, "
        "or retrieve previous incident history."
    )

    st.info(
        f"Selected station: "
        f"**{station_id} — {station_name}**"
    )

    if not is_operator:
        st.caption(
            "Viewer mode: safe read-only agent queries "
            "are available. Operational diagnosis and "
            "status-changing actions are blocked by RBAC."
        )
    
    if (
        "agent_thread_ids"
        not in st.session_state
    ):
        st.session_state.agent_thread_ids = {}


    if (
        station_id
        not in st.session_state.agent_thread_ids
    ):
        st.session_state.agent_thread_ids[
            station_id
        ] = str(
            uuid4()
        )


    thread_id = (
        st.session_state.agent_thread_ids[
            station_id
        ]
    )

    if (
        "pending_approvals"
        not in st.session_state
    ):
        st.session_state.pending_approvals = {}

    st.caption(
        "Conversation thread: "
        f"`{thread_id}`"
    )
    if st.button(
        "➕ New Conversation",
        key=(
            f"new_conversation_"
            f"{station_id}"
        ),
    ):
        new_thread_id = str(
            uuid4()
        )

        st.session_state.agent_thread_ids[
            station_id
        ] = new_thread_id

        st.session_state.chat_histories[
            new_thread_id
        ] = []

        st.rerun()


    if (
        "chat_histories"
        not in st.session_state
    ):
        st.session_state.chat_histories = {}

    if (
        thread_id
        not in st.session_state.chat_histories
    ):
        st.session_state.chat_histories[
            thread_id
        ] = []


    messages = (
        st.session_state.chat_histories[
            thread_id
        ]
    )

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


    pending_approval = (
        st.session_state
        .pending_approvals
        .get(
            thread_id
        )
    )
    
    
    if pending_approval and is_operator:
        st.warning(
            "⚠️ Protected Operation "
            "Requires Approval"
        )
    
        st.write(
            "**Action:** "
            f"{pending_approval['action']}"
        )
    
        st.write(
            "**Station:** "
            f"{pending_approval['station_id']} — "
            f"{pending_approval['station_name']}"
        )
    
        st.write(
            "**Current status:** "
            f"{pending_approval['current_status']}"
        )
    
        st.write(
            "**Requested status:** "
            f"{pending_approval['requested_status']}"
        )
    
        st.caption(
            pending_approval[
                "warning"
            ]
        )
    
        approve_col, reject_col = (
            st.columns(2)
        )
    
        with approve_col:
            if st.button(
                "✅ Approve",
                key=(
                    f"approve_"
                    f"{thread_id}"
                ),
                use_container_width=True,
            ):
                with st.spinner(
                    "Resuming approved workflow..."
                ):
                    result = resume_agent(
                        access_token=access_token,
                        thread_id=thread_id,
                        approved=True,
                    )
    
                st.session_state.pending_approvals.pop(
                    thread_id,
                    None,
                )
    
                if result.get(
                    "approval_required"
                ):
                    st.session_state.pending_approvals[
                        thread_id
                    ] = result[
                        "approval_request"
                    ]
    
                elif result.get(
                    "answer"
                ):
                    messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                result["answer"]
                            ),
                            "tools": result.get(
                                "used_tools",
                                [],
                            ),
                            "trace": result.get(
                                "trace",
                                [],
                            ),
                        }
                    )
    
                st.cache_data.clear()
    
                st.rerun()
    
        with reject_col:
            if st.button(
                "❌ Reject",
                key=(
                    f"reject_"
                    f"{thread_id}"
                ),
                use_container_width=True,
            ):
                with st.spinner(
                    "Cancelling protected action..."
                ):
                    result = resume_agent(
                        access_token=access_token,
                        thread_id=thread_id,
                        approved=False,
                    )
    
                st.session_state.pending_approvals.pop(
                    thread_id,
                    None,
                )
    
                if result.get(
                    "answer"
                ):
                    messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                result["answer"]
                            ),
                            "tools": result.get(
                                "used_tools",
                                [],
                            ),
                            "trace": result.get(
                                "trace",
                                [],
                            ),
                        }
                    )
    
                st.rerun()

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
                    access_token=access_token,
                    station_id=station_id,
                    message=prompt,
                    thread_id=thread_id,
                )
    
                # =================================
                # HUMAN APPROVAL CHECK
                # =================================
    
                if result.get(
                    "approval_required"
                ):
                    st.session_state.pending_approvals[
                        thread_id
                    ] = result[
                        "approval_request"
                    ]
    
                    # Clear cached station data
                    # before rerendering the page.
                    st.cache_data.clear()
    
                    # Rerun Streamlit so the
                    # approval card appears.
                    st.rerun()
    
                # =================================
                # NORMAL COMPLETED RESPONSE
                # =================================
    
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
    
                st.cache_data.clear()
    
            except (
                httpx.HTTPStatusError
            ) as error:
                show_http_error(
                    error
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

                if is_operator:
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
                                    access_token=access_token,
                                    incident_id=incident_id,
                                    status=new_status,
                                )

                                st.cache_data.clear()

                                st.success(
                                    f"Incident "
                                    f"#{incident_id} "
                                    f"updated."
                                )

                                st.rerun()

                            except (
                                httpx.HTTPStatusError
                            ) as error:
                                show_http_error(
                                    error
                                )

                            except httpx.HTTPError as error:
                                st.error(
                                    "Could not update "
                                    "incident status."
                                )

                                st.caption(
                                    str(error)
                                )

                else:
                    st.caption(
                        "Read-only incident view. "
                        "Operator or admin access is required "
                        "to change incident status."
                    )

# =================================================
# Knowledge Base tab
# =================================================


with tab_knowledge:
    st.subheader(
        
            "Knowledge Base Management"
            if is_admin
            else "Knowledge Base"
        
    )

    if is_admin:
        st.write(
            "Upload technical manuals and operational "
            "documents. ChargeOps automatically extracts "
            "the text, chunks it, creates embeddings, "
            "and stores the vectors in PostgreSQL."
        )

    else:
        st.write(
            "Search and review the ChargeOps technical "
            "knowledge base. Document upload and deletion "
            "are restricted to administrators."
        )

    total_documents = len(
        knowledge_documents
    )

    total_chunks = sum(
        document.get(
            "chunk_count",
            0,
        )
        for document
        in knowledge_documents
    )

    knowledge_metric1, knowledge_metric2 = (
        st.columns(2)
    )

    with knowledge_metric1:
        st.metric(
            "Indexed Documents",
            total_documents,
        )

    with knowledge_metric2:
        st.metric(
            "Document Chunks",
            total_chunks,
        )

    st.divider()

    if is_admin:
        # ---------------------------------------------
        # Upload
        # ---------------------------------------------

        st.markdown(
            "### 📤 Upload Document"
        )

        st.caption(
            "Supported formats: PDF, TXT and Markdown. "
            "Maximum file size: 10 MB."
        )

        with st.form(
            "knowledge_upload_form",
            clear_on_submit=True,
        ):
            uploaded_file = st.file_uploader(
                "Choose technical document",
                type=[
                    "pdf",
                    "txt",
                    "md",
                ],
            )

            upload_title = st.text_input(
                "Document title",
                placeholder=(
                    "Example: ABB Terra 54 "
                    "Installation Manual"
                ),
            )

            upload_category = st.text_input(
                "Category",
                value="manual",
                placeholder=(
                    "manual, networking, hardware..."
                ),
            )

            upload_submitted = (
                st.form_submit_button(
                    "Upload and Index",
                    use_container_width=True,
                )
            )

        if upload_submitted:
            if uploaded_file is None:
                st.warning(
                    "Choose a document first."
                )

            else:
                file_title = (
                    upload_title.strip()
                    or uploaded_file.name
                )

                category = (
                    upload_category.strip()
                    or "manual"
                )

                with st.spinner(
                    "Extracting text, creating chunks "
                    "and generating embeddings..."
                ):
                    try:
                        result = (
                            upload_knowledge_document(
                                access_token=access_token,
                                file_name=(
                                    uploaded_file.name
                                ),
                                file_type=(
                                    uploaded_file.type
                                    or (
                                        "application/"
                                        "octet-stream"
                                    )
                                ),
                                file_content=(
                                    uploaded_file
                                    .getvalue()
                                ),
                                title=file_title,
                                category=category,
                            )
                        )

                        st.success(
                            f"Indexed "
                            f"'{result['title']}' "
                            f"with "
                            f"{result['chunk_count']} "
                            f"chunk(s)."
                        )

                        st.cache_data.clear()

                        st.rerun()

                    except (
                        httpx.HTTPStatusError
                    ) as error:
                        if (
                            error.response.status_code
                            == 409
                        ):
                            st.warning(
                                "This document is already "
                                "in the knowledge base."
                            )

                        else:
                            show_http_error(
                                error
                            )

                    except httpx.HTTPError as error:
                        st.error(
                            "Document upload failed."
                        )

                        st.caption(
                            str(error)
                        )

        st.divider()


    else:
        st.info(
            "🔒 Uploading and indexing knowledge documents "
            "requires the admin role."
        )

    # ---------------------------------------------
    # Semantic Search
    # ---------------------------------------------

    st.markdown(
        "### 🔎 Semantic Search"
    )

    st.write(
        "Search the knowledge base by meaning, "
        "not only by exact keywords."
    )

    with st.form(
        "knowledge_search_form"
    ):
        knowledge_query = (
            st.text_input(
                "Search query",
                placeholder=(
                    "Example: charger cable "
                    "becomes extremely hot"
                ),
            )
        )

        search_limit = st.slider(
            "Number of results",
            min_value=1,
            max_value=10,
            value=5,
        )

        search_submitted = (
            st.form_submit_button(
                "Search Knowledge Base"
            )
        )

    if search_submitted:
        if len(
            knowledge_query.strip()
        ) < 3:
            st.warning(
                "Enter a longer search query."
            )

        else:
            with st.spinner(
                "Creating query embedding "
                "and searching pgvector..."
            ):
                try:
                    search_response = (
                        search_knowledge(
                            access_token=access_token,
                            query=(
                                knowledge_query
                                .strip()
                            ),
                            limit=search_limit,
                        )
                    )

                    search_results = (
                        search_response.get(
                            "results",
                            [],
                        )
                    )

                    if not search_results:
                        st.info(
                            "No matching knowledge "
                            "was found."
                        )

                    else:
                        st.success(
                            f"Found "
                            f"{len(search_results)} "
                            f"semantic result(s)."
                        )

                        for index, result in enumerate(
                            search_results,
                            start=1,
                        ):
                            similarity = result.get(
                                "similarity",
                                0.0,
                            )

                            result_title = (
                                result.get(
                                    "title",
                                    "Untitled",
                                )
                            )

                            with st.expander(
                                (
                                    f"{index}. "
                                    f"{result_title} "
                                    f"— "
                                    f"{similarity:.0%}"
                                ),
                                expanded=(
                                    index == 1
                                ),
                            ):
                                meta1, meta2 = (
                                    st.columns(2)
                                )

                                with meta1:
                                    st.write(
                                        "**Category:** "
                                        f"{result.get('category')}"
                                    )

                                with meta2:
                                    st.write(
                                        "**Source:** "
                                        f"{result.get('source')}"
                                    )

                                st.caption(
                                    "Semantic similarity: "
                                    f"{similarity:.4f}"
                                )

                                st.markdown(
                                    "#### Retrieved Chunk"
                                )

                                st.write(
                                    result.get(
                                        "content",
                                        "",
                                    )
                                )

                except (
                    httpx.HTTPStatusError
                ) as error:
                    show_http_error(
                        error
                    )

                except httpx.HTTPError as error:
                    st.error(
                        "Knowledge search failed."
                    )

                    st.caption(
                        str(error)
                    )

    st.divider()

    # ---------------------------------------------
    # Document library
    # ---------------------------------------------

    st.markdown(
        "### 📚 Indexed Documents"
    )

    if not knowledge_documents:
        st.info(
            "No uploaded documents are currently "
            "indexed."
        )

    else:
        for document in knowledge_documents:
            document_id = document[
                "id"
            ]

            title = document[
                "title"
            ]

            chunk_count = document[
                "chunk_count"
            ]

            with st.expander(
                
                    f"{title} — "
                    f"{chunk_count} chunk(s)"
                
            ):
                document_col1, document_col2 = (
                    st.columns(2)
                )

                with document_col1:
                    st.write(
                        "**Category:** "
                        f"{document['category']}"
                    )

                    st.write(
                        "**Status:** "
                        f"{document['status'].title()}"
                    )

                with document_col2:
                    st.write(
                        "**File:** "
                        f"{document['source_filename']}"
                    )

                    st.write(
                        "**Media type:** "
                        f"{document['media_type']}"
                    )

                st.write(
                    "**Document key:** "
                    f"`{document['document_key']}`"
                )

                st.caption(
                    "Created: "
                    f"{document['created_at']}"
                )

                st.divider()

                if is_admin:
                    st.warning(
                        "Deleting this document also "
                        "removes all of its vector chunks."
                    )

                    if st.button(
                        "🗑 Delete Document",
                        key=(
                            f"delete_document_"
                            f"{document_id}"
                        ),
                    ):
                        try:
                            delete_knowledge_document(
                                access_token=access_token,
                                document_id=document_id,
                            )

                            st.cache_data.clear()

                            st.success(
                                f"Deleted '{title}'."
                            )

                            st.rerun()

                        except (
                            httpx.HTTPStatusError
                        ) as error:
                            show_http_error(
                                error
                            )

                        except httpx.HTTPError as error:
                            st.error(
                                "Could not delete "
                                "the document."
                            )

                            st.caption(
                                str(error)
                            )

                else:
                    st.caption(
                        "Document deletion is restricted "
                        "to administrators."
                    )


# =================================================
# System tab
# =================================================

with tab_observability:
    if not is_operator:
        st.info(
            "🔒 Observability is available to "
            "operators and administrators."
        )

    else:
        st.subheader(
            "Agent Observability"
        )

        st.caption(
            "Persistent execution telemetry "
            "for ChargeOps AI."
        )

        try:
            runs = get_agent_runs(
                access_token=access_token,
                station_id=station_id,
                limit=100,
            )

            if not runs:
                st.info(
                    "No agent runs recorded "
                    "for this station yet."
                )

            else:
                total_runs = len(
                    runs
                )

                completed_runs = sum(
                    1
                    for run in runs
                    if run["status"]
                    == "completed"
                )

                approval_runs = sum(
                    1
                    for run in runs
                    if run[
                        "approval_required"
                    ]
                )

                latencies = [
                    run["latency_ms"]
                    for run in runs
                ]

                average_latency = (
                    sum(latencies)
                    / len(latencies)
                )

                total_tool_calls = sum(
                    len(
                        run[
                            "used_tools"
                        ]
                    )
                    for run in runs
                )

                (
                    metric1,
                    metric2,
                    metric3,
                    metric4,
                ) = st.columns(4)

                metric1.metric(
                    "Runs",
                    total_runs,
                )

                metric2.metric(
                    "Completed",
                    completed_runs,
                )

                metric3.metric(
                    "Avg Latency",
                    (
                        f"{average_latency:,.0f} ms"
                    ),
                )

                metric4.metric(
                    "Tool Calls",
                    total_tool_calls,
                )

                st.markdown(
                    "### Human Approval"
                )

                st.metric(
                    "Protected Runs",
                    approval_runs,
                )

                st.markdown(
                    "### Recent Agent Runs"
                )

                table_rows = []

                for run in runs:
                    approval = "—"

                    if (
                        run[
                            "approval_decision"
                        ]
                        is True
                    ):
                        approval = (
                            "Approved"
                        )

                    elif (
                        run[
                            "approval_decision"
                        ]
                        is False
                    ):
                        approval = (
                            "Rejected"
                        )

                    elif run[
                        "approval_required"
                    ]:
                        approval = (
                            "Pending"
                        )

                    table_rows.append(
                        {
                            "Run ID": str(
                                run["id"]
                            )[:8],
                            "Status": (
                                run[
                                    "status"
                                ]
                            ),
                            "Latency": (
                                f"{run['latency_ms']} ms"
                            ),
                            "Tools": ", ".join(
                                run[
                                    "used_tools"
                                ]
                            )
                            or "None",
                            "Approval": (
                                approval
                            ),
                            "Started": (
                                run[
                                    "started_at"
                                ]
                            ),
                        }
                    )

                st.dataframe(
                    table_rows,
                    use_container_width=True,
                    hide_index=True,
                )

                st.markdown(
                    "### Run Inspector"
                )

                run_options = {
                    (
                        f"{str(run['id'])[:8]}"
                        " — "
                        f"{run['status']}"
                        " — "
                        f"{run['latency_ms']} ms"
                    ): run
                    for run in runs
                }

                selected_label = (
                    st.selectbox(
                        "Select execution",
                        options=list(
                            run_options.keys()
                        ),
                    )
                )

                selected_run = (
                    run_options[
                        selected_label
                    ]
                )

                st.write(
                    "**Run ID:**",
                    selected_run["id"],
                )

                st.write(
                    "**Thread ID:**",
                    selected_run[
                        "thread_id"
                    ],
                )

                st.write(
                    "**Model:**",
                    selected_run[
                        "model"
                    ],
                )

                st.write(
                    "**User request:**"
                )

                st.code(
                    selected_run[
                        "user_message"
                    ]
                )

                st.write(
                    "**Used tools:**",
                    selected_run[
                        "used_tools"
                    ],
                )

                st.write(
                    "**Agent answer:**"
                )

                st.write(
                    selected_run[
                        "answer"
                    ]
                    or "Workflow has not "
                    "completed yet."
                )

                with st.expander(
                    "Execution trace"
                ):
                    st.json(
                        selected_run[
                            "trace"
                        ]
                    )

        except httpx.HTTPError as error:
            st.error(
                "Could not load "
                "observability data."
            )

            st.caption(
                str(error)
            )

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
  ├── Knowledge Management
  │       │
  │       ├── PDF / TXT / MD
  │       ├── Text Extraction
  │       ├── Chunking
  │       ├── OpenAI Embeddings
  │       └── pgvector
  │
  └── ChargeOps Agent — LangGraph
          │
          ├── PostgreSQL Checkpointer
          │       ↓
          │    thread_id
          │       ↓
          │    Conversation State
          │
          ↓
      call_model
          │
      tool call?
       /      \
     yes       no
      ↓         ↓
execute_tools   END
      │
      └────────→ call_model
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

    stack1, stack2, stack3, stack4 = (
        st.columns(4)
    )

    with stack1:
        st.markdown(
            """
### AI

- OpenAI Responses API
- Structured Outputs
- Function Calling
- Multi-tool Agent
- LangGraph StateGraph
- Conditional Routing
- Runtime Context
- RAG
- Embeddings
- PostgreSQL Checkpointing
- Thread-scoped Memory
- Persistent Conversation State
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
- Alembic
            """
        )

    with stack3:
        st.markdown(
            """
### Data

- PostgreSQL
- pgvector
- HNSW
- Semantic Search
- Incident Memory
            """
        )

    with stack4:
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
Performs semantic retrieval across EV charging manuals and technical knowledge using embeddings and pgvector.

**5. `diagnose_charging_issue`**  
Performs structured, knowledge-grounded fault analysis and records the resulting incident.
        """
    )
