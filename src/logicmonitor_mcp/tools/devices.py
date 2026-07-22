import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import LogicMonitorClient, LogicMonitorError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], LogicMonitorClient | None]) -> None:

    @mcp.tool()
    async def logicmonitor_get_devices(
        size: int = 100,
        offset: int = 0,
        sort: str | None = None,
        filter: str | None = None,
        fields: str | None = None,
    ) -> str:
        """List monitored devices for the portal.

        API: GET /device/devices

        Args:
            size: Page size (default 100).
            offset: Pagination offset (default 0).
            sort: Optional sort expression (e.g. "+id", "-hostStatus").
            filter: Optional LogicMonitor filter expression (e.g. "displayName:host1").
            fields: Optional comma-separated list of fields to return.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                "/device/devices",
                params={"size": size, "offset": offset, "sort": sort, "filter": filter, "fields": fields},
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def logicmonitor_get_device_groups(
        size: int = 100,
        offset: int = 0,
        sort: str | None = None,
        filter: str | None = None,
        fields: str | None = None,
    ) -> str:
        """List device groups for the portal.

        API: GET /device/groups

        Args:
            size: Page size (default 100).
            offset: Pagination offset (default 0).
            sort: Optional sort expression.
            filter: Optional LogicMonitor filter expression.
            fields: Optional comma-separated list of fields to return.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                "/device/groups",
                params={"size": size, "offset": offset, "sort": sort, "filter": filter, "fields": fields},
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def logicmonitor_get_device_properties(
        device_id: str,
        size: int = 100,
        offset: int = 0,
        filter: str | None = None,
    ) -> str:
        """List custom and system properties for a specific device.

        API: GET /device/devices/{deviceId}/properties

        Args:
            device_id: Device ID.
            size: Page size (default 100).
            offset: Pagination offset (default 0).
            filter: Optional LogicMonitor filter expression.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                f"/device/devices/{device_id}/properties",
                params={"size": size, "offset": offset, "filter": filter},
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"
