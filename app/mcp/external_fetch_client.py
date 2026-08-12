import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import (
    asynccontextmanager,
)
from typing import (
    Literal,
)
from urllib.parse import urlparse

from mcp import (
    Client,
    StdioServerParameters,
    types,
)
from mcp.client.stdio import (
    stdio_client,
)
from mcp.shared.exceptions import (
    MCPError,
)

from app.core.config import settings

logger = logging.getLogger(
    __name__
)


class ExternalMCPError(
    Exception
):
    """
    Raised when an optional external MCP
    capability cannot be used safely.
    """


ExternalReferenceSource = Literal[
    "oca_ocpp_overview",
    "oca_ocpp_downloads",
    "oca_certification",
]


EXTERNAL_REFERENCE_URLS: dict[
    ExternalReferenceSource,
    str,
] = {
    "oca_ocpp_overview": (
        "https://openchargealliance.org/"
        "protocols/ocpp-protocols/"
    ),
    "oca_ocpp_downloads": (
        "https://openchargealliance.org/"
        "my-oca/ocpp/"
    ),
    "oca_certification": (
        "https://openchargealliance.org/"
        "certificationocpp/"
    ),
}


def resolve_external_reference_source(
    source: ExternalReferenceSource,
) -> str:
    return EXTERNAL_REFERENCE_URLS[
        source
    ]


def validate_external_reference_url(
    url: str,
) -> str:
    """
    Apply a deterministic outbound security
    policy before invoking an external MCP
    network-capable tool.
    """

    if len(url) > 2048:
        raise ExternalMCPError(
            "External reference URL is too long."
        )

    parsed = urlparse(
        url
    )

    if parsed.scheme != "https":
        raise ExternalMCPError(
            "External MCP references "
            "must use HTTPS."
        )

    if (
        parsed.username is not None
        or parsed.password is not None
    ):
        raise ExternalMCPError(
            "Credentials are not allowed "
            "in external reference URLs."
        )

    if (
        parsed.port is not None
        and parsed.port != 443
    ):
        raise ExternalMCPError(
            "Non-standard external ports "
            "are not allowed."
        )

    hostname = (
        parsed.hostname
        or ""
    ).lower()

    allowed = (
        settings
        .external_mcp_allowed_hosts_list
    )

    host_allowed = any(
        (
            hostname
            == allowed_host
        )
        or hostname.endswith(
            f".{allowed_host}"
        )
        for allowed_host in allowed
    )

    if not host_allowed:
        raise ExternalMCPError(
            "External reference host "
            "is not allowlisted."
        )

    return url


@asynccontextmanager
async def open_external_fetch_client(
) -> AsyncIterator[
    Client
]:
    """
    Start the official Fetch MCP server in
    its own dependency-isolated environment.

    ChargeOps itself remains on MCP v2.

    The reference Fetch server currently needs
    MCP <2, so uvx isolates that dependency
    instead of downgrading ChargeOps.
    """

    server = StdioServerParameters(
        command="uvx",
        args=[
            "--with",
            "mcp<2",
            "mcp-server-fetch==2026.7.10",
        ],
    )

    async with Client(
        stdio_client(
            server
        )
    ) as client:
        yield client


async def discover_external_fetch_tools(
) -> set[str]:
    try:
        async with asyncio.timeout(
            settings
            .external_mcp_timeout_seconds
        ):
            async with (
                open_external_fetch_client()
                as client
            ):
                response = (
                    await client.list_tools()
                )

                return {
                    tool.name
                    for tool
                    in response.tools
                }

    except (
        TimeoutError,
        OSError,
        MCPError,
    ) as error:
        raise ExternalMCPError(
            "External MCP server "
            "is unavailable."
        ) from error


async def fetch_external_reference(
    source: ExternalReferenceSource,
) -> dict[
    str,
    str | bool,
]:
    url = (
        resolve_external_reference_source(
            source
        )
    )

    safe_url = (
        validate_external_reference_url(
            url
        )
    )

    try:
        async with asyncio.timeout(
            settings
            .external_mcp_timeout_seconds
        ):
            async with (
                open_external_fetch_client()
                as client
            ):
                tools_response = (
                    await client.list_tools()
                )

                tool_names = {
                    tool.name
                    for tool
                    in tools_response.tools
                }

                if "fetch" not in tool_names:
                    raise ExternalMCPError(
                        "External MCP server "
                        "does not expose the "
                        "required fetch tool."
                    )

                result = await client.call_tool(
                    "fetch",
                    {
                        "url": safe_url,
                        "max_length": (
                            settings
                            .external_mcp_max_content_chars
                        ),
                        "start_index": 0,
                        "raw": False,
                    },
                    read_timeout_seconds=(
                        settings
                        .external_mcp_timeout_seconds
                    ),
                )

    except ExternalMCPError:
        raise

    except TimeoutError as error:
        logger.warning(
            "External MCP fetch timed out."
        )

        raise ExternalMCPError(
            "External MCP reference "
            "timed out."
        ) from error

    except (
        OSError,
        MCPError,
    ) as error:
        logger.exception(
            "External MCP fetch failed."
        )

        raise ExternalMCPError(
            "External MCP reference "
            "is temporarily unavailable."
        ) from error

    if result.is_error:
        raise ExternalMCPError(
            "External MCP fetch tool "
            "reported a failure."
        )

    text_parts = [
        block.text
        for block in result.content
        if isinstance(
            block,
            types.TextContent,
        )
    ]

    content = "\n".join(
        text_parts
    ).strip()

    if not content:
        raise ExternalMCPError(
            "External MCP fetch returned "
            "no usable text."
        )

    content = content[
        : settings
        .external_mcp_max_content_chars
    ]

    return {
        "available": True,
        "source": source,
        "source_url": safe_url,
        "trust_level": (
            "external_untrusted_reference"
        ),
        "content": content,
    }