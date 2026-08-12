import asyncio
from contextlib import (
    asynccontextmanager,
)
from types import SimpleNamespace
from unittest.mock import (
    AsyncMock,
    patch,
)

import pytest
from mcp import types

from app.mcp.external_fetch_client import (
    ExternalMCPError,
    discover_external_fetch_tools,
    fetch_external_reference,
    validate_external_reference_url,
)
from app.services.agent_tools import (
    TOOLS,
    execute_external_reference_tool,
)


class FakeExternalClient:
    def __init__(
        self,
        *,
        tools: list[str],
        result=None,
    ) -> None:
        self.tool_names = tools

        self.result = (
            result
            if result is not None
            else SimpleNamespace(
                is_error=False,
                content=[
                    types.TextContent(
                        type="text",
                        text=(
                            "Official OCPP "
                            "reference content."
                        ),
                    )
                ],
            )
        )

        self.call_tool = AsyncMock(
            return_value=self.result
        )

    async def list_tools(
        self,
    ):
        return SimpleNamespace(
            tools=[
                SimpleNamespace(
                    name=name
                )
                for name
                in self.tool_names
            ]
        )


def make_client_context(
    client: FakeExternalClient,
):
    @asynccontextmanager
    async def context():
        yield client

    return context


def test_external_tool_is_registered(
) -> None:
    names = {
        tool["name"]
        for tool in TOOLS
    }

    assert (
        "fetch_external_ev_reference"
        in names
    )


def test_external_url_allows_oca(
) -> None:
    url = (
        "https://"
        "openchargealliance.org/"
        "protocols/ocpp-protocols/"
    )

    assert (
        validate_external_reference_url(
            url
        )
        == url
    )


def test_external_url_rejects_unapproved_host(
) -> None:
    with pytest.raises(
        ExternalMCPError
    ):
        validate_external_reference_url(
            "https://example.com/"
        )


def test_external_mcp_discovers_fetch_tool(
) -> None:
    async def run_test() -> None:
        fake_client = (
            FakeExternalClient(
                tools=[
                    "fetch",
                ]
            )
        )

        context = (
            make_client_context(
                fake_client
            )
        )

        with patch(
            "app.mcp."
            "external_fetch_client."
            "open_external_fetch_client",
            new=context,
        ):
            tools = (
                await discover_external_fetch_tools()
            )

        assert "fetch" in tools

    asyncio.run(
        run_test()
    )


def test_external_mcp_fetch_calls_discovered_tool(
) -> None:
    async def run_test() -> None:
        fake_client = (
            FakeExternalClient(
                tools=[
                    "fetch",
                ]
            )
        )

        context = (
            make_client_context(
                fake_client
            )
        )

        with patch(
            "app.mcp."
            "external_fetch_client."
            "open_external_fetch_client",
            new=context,
        ):
            result = (
                await fetch_external_reference(
                    "oca_ocpp_overview"
                )
            )

        assert (
            result["available"]
            is True
        )

        assert (
            result["trust_level"]
            == (
                "external_untrusted_reference"
            )
        )

        fake_client.call_tool.assert_awaited_once()

    asyncio.run(
        run_test()
    )


def test_external_tool_degrades_safely(
) -> None:
    async def run_test() -> None:
        with patch(
            "app.services.agent_tools."
            "fetch_external_reference",
            new=AsyncMock(
                side_effect=(
                    ExternalMCPError(
                        "internal provider failure"
                    )
                )
            ),
        ):
            result, trace = (
                await execute_external_reference_tool(
                    "oca_ocpp_overview"
                )
            )

        assert (
            result["available"]
            is False
        )

        assert trace.status == "error"

        assert (
            "internal provider failure"
            not in str(result)
        )

    asyncio.run(
        run_test()
    )