import asyncio
from types import SimpleNamespace
from unittest.mock import (
    AsyncMock,
    patch,
)

from app.agents.standards_specialist import (
    run_standards_specialist,
)
from app.services.agent_tools import (
    TOOLS,
    execute_standards_specialist_tool,
)


def make_function_call():
    return SimpleNamespace(
        type="function_call",
        name="get_oca_reference",
        arguments=(
            '{"source":"oca_ocpp_overview"}'
        ),
        call_id="call-1",
        to_dict=lambda: {
            "type": "function_call",
            "name": "get_oca_reference",
            "arguments": (
                '{"source":"oca_ocpp_overview"}'
            ),
            "call_id": "call-1",
        },
    )


def test_standards_specialist_is_registered(
) -> None:
    tool_names = {
        tool["name"]
        for tool in TOOLS
    }

    assert (
        "consult_standards_specialist"
        in tool_names
    )


def test_standards_specialist_uses_external_mcp_reference(
) -> None:
    async def run_test() -> None:
        first_response = (
            SimpleNamespace(
                output=[
                    make_function_call()
                ],
                output_text="",
            )
        )

        second_response = (
            SimpleNamespace(
                output=[],
                output_text=(
                    "The current official OCA "
                    "reference confirms the "
                    "requested OCPP information."
                ),
            )
        )

        create_mock = AsyncMock(
            side_effect=[
                first_response,
                second_response,
            ]
        )

        fetch_mock = AsyncMock(
            return_value={
                "available": True,
                "source": (
                    "oca_ocpp_overview"
                ),
                "source_url": (
                    "https://"
                    "openchargealliance.org/"
                    "protocols/"
                    "ocpp-protocols/"
                ),
                "trust_level": (
                    "external_untrusted_reference"
                ),
                "content": (
                    "Official OCPP "
                    "reference content."
                ),
            }
        )

        with (
            patch(
                "app.agents."
                "standards_specialist."
                "client.responses.create",
                new=create_mock,
            ),
            patch(
                "app.agents."
                "standards_specialist."
                "fetch_external_reference",
                new=fetch_mock,
            ),
        ):
            result = (
                await run_standards_specialist(
                    "What OCPP versions are "
                    "currently supported?"
                )
            )

        assert (
            result["available"]
            is True
        )

        assert (
            result["agent"]
            == "standards_specialist"
        )

        assert len(
            result["sources"]
        ) == 1

        assert (
            create_mock.await_count
            == 2
        )

        fetch_mock.assert_awaited_once()

    asyncio.run(
        run_test()
    )


def test_specialist_executor_returns_delegated_result(
) -> None:
    async def run_test() -> None:
        with patch(
            "app.services.agent_tools."
            "run_standards_specialist",
            new=AsyncMock(
                return_value={
                    "available": True,
                    "agent": (
                        "standards_specialist"
                    ),
                    "answer": (
                        "Specialist finding."
                    ),
                    "sources": [
                        (
                            "https://"
                            "openchargealliance.org/"
                        )
                    ],
                }
            ),
        ):
            result, trace = (
                await execute_standards_specialist_tool(
                    "Research current OCPP."
                )
            )

        assert (
            result["available"]
            is True
        )

        assert (
            trace.tool
            == (
                "consult_standards_specialist"
            )
        )

        assert (
            trace.status
            == "success"
        )

    asyncio.run(
        run_test()
    )