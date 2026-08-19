from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import LogicMonitorClient, LogicMonitorError
from ._common import DEFAULT_PAGE_SIZE, NO_TOKEN, clamp_size


def register(mcp: FastMCP, client_factory: Callable[[], LogicMonitorClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def logicmonitor_get_users(
        size: Annotated[
            int, Field(description="Page size (default 50, max 1000).")
        ] = DEFAULT_PAGE_SIZE,
        offset: Annotated[int, Field(description="Pagination offset (default 0).")] = 0,
        filter: Annotated[
            str | None, Field(description='LogicMonitor filter expression, e.g. "username:jdoe".')
        ] = None,
        fields: Annotated[
            str | None, Field(description="Comma-separated list of fields to return.")
        ] = None,
    ) -> str:
        """List portal user (admin) accounts."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                "/setting/admins",
                params={
                    "size": clamp_size(size),
                    "offset": offset,
                    "filter": filter,
                    "fields": fields,
                },
            )
            return dump_json_capped(result)
        except LogicMonitorError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def logicmonitor_get_roles(
        size: Annotated[
            int, Field(description="Page size (default 50, max 1000).")
        ] = DEFAULT_PAGE_SIZE,
        offset: Annotated[int, Field(description="Pagination offset (default 0).")] = 0,
        filter: Annotated[
            str | None, Field(description="LogicMonitor filter expression.")
        ] = None,
    ) -> str:
        """List roles (permission sets) configured for the portal."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                "/setting/roles",
                params={"size": clamp_size(size), "offset": offset, "filter": filter},
            )
            return dump_json_capped(result)
        except LogicMonitorError as e:
            return e.to_envelope()
