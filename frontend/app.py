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
    latitude: float,
    longitude: float,
    message: str,
) -> dict:
    response = httpx.post(
        f"{API_BASE_URL}/agent/run",
        json={
            "station_id": station_id,
            "latitude": latitude,
            "longitude": longitude,
            "message": message,
        },
        timeout=60.0,
    )

    response.raise_for_status()

    return response.json()


st.title("⚡ ChargeOps AI")

st.caption(
    "Agentic EV Charging Intelligence & Operations Platform"
)


with st.sidebar:
    st.header("Station Context")

    station_id = st.text_input(
        "Station ID",
        value="KL-205",
    )

    latitude = st.number_input(
        "Latitude",
        value=3.1390,
        format="%.6f",
    )

    longitude = st.number_input(
        "Longitude",
        value=101.6869,
        format="%.6f",
    )

    st.divider()

    if check_backend():
        st.success("Backend connected")
    else:
        st.error("Backend unavailable")


tab_agent, tab_about = st.tabs(
    [
        "🤖 AI Agent",
        "ℹ️ System",
    ]
)


with tab_agent:
    st.subheader("Ask ChargeOps")

    st.write(
        "Ask operational questions about this charging station. "
        "The agent can decide whether it needs external tools."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message.get("tools"):
                st.caption(
                    "Tools used: "
                    + ", ".join(message["tools"])
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

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"), st.spinner(
            "ChargeOps AI is analyzing..."
        ):
            try:
                result = run_agent(
                    station_id=station_id,
                    latitude=latitude,
                    longitude=longitude,
                    message=prompt,
                )

                answer = result["answer"]
                tools = result["used_tools"]

                st.markdown(answer)

                if tools:
                    st.caption(
                        "🔧 Tools used: "
                        + ", ".join(tools)
                    )
                else:
                    st.caption(
                        "💬 No external tools required"
                    )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "tools": tools,
                    }
                )

            except httpx.HTTPStatusError as error:
                st.error(
                    f"Backend error: "
                    f"{error.response.status_code}"
                )

            except httpx.HTTPError:
                st.error(
                    "Could not connect to the ChargeOps backend."
                )


with tab_about:
    st.subheader("Current Architecture")

    st.code(
        """
Streamlit
    ↓
FastAPI
    ↓
ChargeOps Agent
    ↓
OpenAI
    ↓
Tool Decision
    ├── Weather API
    └── Direct Answer
        """
    )

    st.subheader("Current Capabilities")

    st.markdown(
        """
- Generative AI chat
- Structured EV fault analysis
- Real-time weather integration
- Tool-calling agent
- Automatic tool selection
- Input validation
- Error handling
- Automated testing
        """
    )