import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import LogicMonitorClient, LogicMonitorError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], LogicMonitorClient | None]) -> None:

    @mcp.tool()
    async def logicmonitor_get_users(
        size: int = 100,
        offset: int = 0,
        filter: str | None = None,
        fields: str | None = None,
    ) -> str:
        """List portal user (admin) accounts.

        API: GET /setting/admins

        Args:
            size: Page size (default 100).
            offset: Pagination offset (default 0).
            filter: Optional LogicMonitor filter expression (e.g. "username:jdoe").
            fields: Optional comma-separated list of fields to return.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                "/setting/admins",
                params={"size": size, "offset": offset, "filter": filter, "fields": fields},
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def logicmonitor_get_roles(
        size: int = 100,
        offset: int = 0,
        filter: str | None = None,
    ) -> str:
        """List roles (permission sets) configured for the portal.

        API: GET /setting/roles

        Args:
            size: Page size (default 100).
            offset: Pagination offset (default 0).
            filter: Optional LogicMonitor filter expression.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                "/setting/roles", params={"size": size, "offset": offset, "filter": filter}
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"
