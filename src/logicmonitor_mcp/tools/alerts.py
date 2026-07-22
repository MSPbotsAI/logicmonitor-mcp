import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import LogicMonitorClient, LogicMonitorError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], LogicMonitorClient | None]) -> None:

    @mcp.tool()
    async def logicmonitor_get_alerts(
        size: int = 50,
        offset: int = 0,
        sort: str | None = None,
        filter: str | None = None,
        fields: str | None = None,
    ) -> str:
        """List active/historical alerts for the portal.

        API: GET /alert/alerts

        Args:
            size: Page size (default 50).
            offset: Pagination offset (default 0).
            sort: Optional sort expression (e.g. "-startEpoch").
            filter: Optional LogicMonitor filter expression (e.g. "severity:4").
            fields: Optional comma-separated list of fields to return.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                "/alert/alerts",
                params={"size": size, "offset": offset, "sort": sort, "filter": filter, "fields": fields},
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def logicmonitor_get_alert_detail(alert_id: str) -> str:
        """Get full detail for a specific alert.

        API: GET /alert/alerts/{id}

        Args:
            alert_id: Alert ID (e.g. "ES21935402").
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(f"/alert/alerts/{alert_id}")
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def logicmonitor_get_alert_rules(
        size: int = 100,
        offset: int = 0,
        filter: str | None = None,
    ) -> str:
        """List alert escalation rules configured for the portal.

        API: GET /setting/alert/rules

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
                "/setting/alert/rules", params={"size": size, "offset": offset, "filter": filter}
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"
