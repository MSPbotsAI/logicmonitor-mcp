import contextvars
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .api_client import LogicMonitorClient
from .config import Settings

# Per-request credential isolation via contextvars.
# GatewayTokenMiddleware sets this before the MCP handler runs.
# Python asyncio copies context per task, so concurrent SSE connections are isolated.
# Value is (company, access_id, access_key).
_gateway_creds_var: contextvars.ContextVar[tuple[str, str, str] | None] = contextvars.ContextVar(
    "logicmonitor_gateway_creds", default=None
)

REQUIRED_HEADERS = ["X-LogicMonitor-Company", "X-LogicMonitor-Access-Id", "X-LogicMonitor-Access-Key"]


def get_client_from_context() -> LogicMonitorClient | None:
    """Resolve the active LogicMonitorClient for the current request context."""
    creds = _gateway_creds_var.get()
    if not creds:
        return None
    company, access_id, access_key = creds
    return LogicMonitorClient(company=company, access_id=access_id, access_key=access_key)


class GatewayTokenMiddleware:
    """ASGI middleware.

    Reads X-LogicMonitor-Company, X-LogicMonitor-Access-Id, and
    X-LogicMonitor-Access-Key (all required) from request headers and stores
    them in the contextvar for the duration of the request. Returns 401 if
    any of the three is missing on /mcp requests.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/mcp"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        company = request.headers.get("x-logicmonitor-company")
        access_id = request.headers.get("x-logicmonitor-access-id")
        access_key = request.headers.get("x-logicmonitor-access-key")
        if not company or not access_id or not access_key:
            response = JSONResponse(
                {
                    "error": "Missing credentials",
                    "message": (
                        "This server requires the X-LogicMonitor-Company, "
                        "X-LogicMonitor-Access-Id, and X-LogicMonitor-Access-Key headers"
                    ),
                    "required_headers": REQUIRED_HEADERS,
                },
                status_code=401,
            )
            await response(scope, receive, send)
            return

        ctx_token = _gateway_creds_var.set((company, access_id, access_key))
        try:
            await self.app(scope, receive, send)
        finally:
            _gateway_creds_var.reset(ctx_token)


def create_mcp_server(settings: Settings) -> FastMCP:
    """Build the FastMCP server instance and register all LogicMonitor tools."""
    # DNS-rebinding protection is a browser-oriented safeguard that rejects
    # non-localhost Host headers with 421. Disable it so the server works
    # correctly behind a reverse proxy or docker network.
    mcp = FastMCP(
        name="logicmonitor-mcp",
        instructions=(
            "LogicMonitor is a SaaS infrastructure monitoring platform. Devices "
            "(servers, network gear, cloud resources) are organized into device "
            "groups and monitored via DataSources, which collect metrics and raise "
            "Alerts when thresholds are breached; escalation rules control who "
            "gets notified. Scheduled Down Time (SDT) suppresses alerts during "
            "planned maintenance. Admin covers portal users/roles; Reports "
            "summarizes configured reports for stakeholders.\n\n"
            "Tool domains: devices (list devices/device groups, device "
            "properties), datasources (DataSources applied to a device, "
            "collected data points), alerts (list/inspect alerts and "
            "escalation rules), sdt (scheduled maintenance windows), admin "
            "(users, roles), reports (reports, report groups).\n\n"
            "Typical flow: logicmonitor_get_devices to find a device_id, then "
            "logicmonitor_get_device_datasources(device_id) to see what's "
            "monitored on it, then logicmonitor_get_device_datasource_data to "
            "pull that DataSource's collected data points. Before treating a "
            "missing alert as a false negative, check logicmonitor_get_sdts — "
            "it may be suppressed by an active maintenance window. All 13 "
            "tools are read-only queries; there are no write/delete tools in "
            "this service."
        ),
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        stateless_http=True,
        json_response=True,
    )

    client_factory: Callable[[], LogicMonitorClient | None] = get_client_from_context

    from .tools import admin, alerts, datasources, devices, reports, sdt

    devices.register(mcp, client_factory)
    datasources.register(mcp, client_factory)
    alerts.register(mcp, client_factory)
    admin.register(mcp, client_factory)
    reports.register(mcp, client_factory)
    sdt.register(mcp, client_factory)

    return mcp
