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
    async def logicmonitor_get_alerts(
        size: Annotated[
            int, Field(description="Page size (default 50, max 1000).")
        ] = DEFAULT_PAGE_SIZE,
        offset: Annotated[int, Field(description="Pagination offset (default 0).")] = 0,
        sort: Annotated[
            str | None, Field(description='Sort expression, e.g. "-startEpoch".')
        ] = None,
        filter: Annotated[
            str | None, Field(description='LogicMonitor filter expression, e.g. "severity:4".')
        ] = None,
        fields: Annotated[
            str | None, Field(description="Comma-separated list of fields to return.")
        ] = None,
    ) -> str:
        """List active/historical alerts for the portal."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                "/alert/alerts",
                params={
                    "size": clamp_size(size),
                    "offset": offset,
                    "sort": sort,
                    "filter": filter,
                    "fields": fields,
                },
            )
            return dump_json_capped(result)
        except LogicMonitorError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def logicmonitor_get_alert_detail(
        alert_id: Annotated[str, Field(description='Alert ID, e.g. "ES21935402".')],
    ) -> str:
        """Get full detail for a specific alert."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(f"/alert/alerts/{alert_id}")
            return dump_json_capped(result)
        except LogicMonitorError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def logicmonitor_get_alert_rules(
        size: Annotated[
            int, Field(description="Page size (default 50, max 1000).")
        ] = DEFAULT_PAGE_SIZE,
        offset: Annotated[int, Field(description="Pagination offset (default 0).")] = 0,
        filter: Annotated[
            str | None, Field(description="LogicMonitor filter expression.")
        ] = None,
    ) -> str:
        """List alert escalation rules configured for the portal."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                "/setting/alert/rules",
                params={"size": clamp_size(size), "offset": offset, "filter": filter},
            )
            return dump_json_capped(result)
        except LogicMonitorError as e:
            return e.to_envelope()
