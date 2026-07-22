import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import LogicMonitorClient, LogicMonitorError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], LogicMonitorClient | None]) -> None:

    @mcp.tool()
    async def logicmonitor_get_sdts(
        size: int = 100,
        offset: int = 0,
        filter: str | None = None,
    ) -> str:
        """List Scheduled Down Time (SDT) entries for the portal.

        API: GET /sdt/sdts

        Args:
            size: Page size (default 100).
            offset: Pagination offset (default 0).
            filter: Optional LogicMonitor filter expression (e.g. "type:DeviceSDT").
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                "/sdt/sdts", params={"size": size, "offset": offset, "filter": filter}
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"
