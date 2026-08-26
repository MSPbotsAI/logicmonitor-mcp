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
    async def logicmonitor_get_device_datasources(
        device_id: Annotated[str, Field(description="Device ID.")],
        size: Annotated[
            int, Field(description="Page size (default 50, max 1000).")
        ] = DEFAULT_PAGE_SIZE,
        offset: Annotated[int, Field(description="Pagination offset (default 0).")] = 0,
        filter: Annotated[
            str | None, Field(description="LogicMonitor filter expression.")
        ] = None,
        fields: Annotated[
            str | None, Field(description="Comma-separated list of fields to return.")
        ] = None,
    ) -> str:
        """List the DataSources applied to a specific device."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                f"/device/devices/{device_id}/devicedatasources",
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
    async def logicmonitor_get_device_datasource_data(
        device_id: Annotated[str, Field(description="Device ID.")],
        source_id: Annotated[str, Field(description="Device DataSource ID.")],
        start: Annotated[
            int | None, Field(description="Start epoch time in seconds.")
        ] = None,
        end: Annotated[int | None, Field(description="End epoch time in seconds.")] = None,
    ) -> str:
        """Get collected data points for a device DataSource."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                f"/device/devices/{device_id}/devicedatasources/{source_id}/data",
                params={"start": start, "end": end},
            )
            return dump_json_capped(result)
        except LogicMonitorError as e:
            return e.to_envelope()
