import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import LogicMonitorClient, LogicMonitorError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], LogicMonitorClient | None]) -> None:

    @mcp.tool()
    async def logicmonitor_get_device_datasources(
        device_id: str,
        size: int = 100,
        offset: int = 0,
        filter: str | None = None,
        fields: str | None = None,
    ) -> str:
        """List the datasources applied to a specific device.

        API: GET /device/devices/{deviceId}/devicedatasources

        Args:
            device_id: Device ID.
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
                f"/device/devices/{device_id}/devicedatasources",
                params={"size": size, "offset": offset, "filter": filter, "fields": fields},
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def logicmonitor_get_device_datasource_instances(
        device_id: str,
        source_id: str,
        size: int = 100,
        offset: int = 0,
        filter: str | None = None,
    ) -> str:
        """List the instances of a device datasource on a specific device.

        API: GET /device/devices/{deviceId}/devicedatasources/{sourceId}/instances

        Args:
            device_id: Device ID.
            source_id: Device datasource ID (the "id" from get_device_datasources).
            size: Page size (default 100).
            offset: Pagination offset (default 0).
            filter: Optional LogicMonitor filter expression.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                f"/device/devices/{device_id}/devicedatasources/{source_id}/instances",
                params={"size": size, "offset": offset, "filter": filter},
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def logicmonitor_get_device_datasource_data(
        device_id: str,
        source_id: str,
        start: int | None = None,
        end: int | None = None,
    ) -> str:
        """Get collected data points for a device datasource.

        API: GET /device/devices/{deviceId}/devicedatasources/{sourceId}/data

        Args:
            device_id: Device ID.
            source_id: Device datasource ID.
            start: Optional start epoch time (seconds).
            end: Optional end epoch time (seconds).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                f"/device/devices/{device_id}/devicedatasources/{source_id}/data",
                params={"start": start, "end": end},
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def logicmonitor_get_device_datasource_instance_alertsettings(
        device_id: str,
        source_id: str,
        instance_id: str,
    ) -> str:
        """Get alert threshold/settings overrides for a device datasource instance.

        API: GET /device/devices/{deviceId}/devicedatasources/{sourceId}/instances/{instanceId}/alertsettings

        Args:
            device_id: Device ID.
            source_id: Device datasource ID.
            instance_id: Device datasource instance ID.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                f"/device/devices/{device_id}/devicedatasources/{source_id}"
                f"/instances/{instance_id}/alertsettings"
            )
            return json.dumps(result, indent=2)
        except LogicMonitorError as e:
            return f"Error: {e}"
