import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import LogicMonitorClient, LogicMonitorError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], LogicMonitorClient | None]) -> None:

    @mcp.tool()
    async def logicmonitor_get_reports(
        size: int = 100,
        offset: int = 0,
        filter: str | None = None,
        fields: str | None = None,
    ) -> str:
        """List reports configured for the portal.

        API: GET /report/reports

        Args:
            size: Page size (default 100).
            offset: Pagination offset (default 0).
            filter: Optional LogicMonitor filter expression.
            fields: Optional comma-separated list of fields to return.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                "/report/reports",
                params={"size": size, "offset": offset, "filter": filter, "fields": fields},
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def logicmonitor_get_report_groups(
        size: int = 100,
        offset: int = 0,
        filter: str | None = None,
    ) -> str:
        """List report groups configured for the portal.

        API: GET /report/groups

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
                "/report/groups", params={"size": size, "offset": offset, "filter": filter}
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"
