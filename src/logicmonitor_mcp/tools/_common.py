from .._json import error_envelope

# LogicMonitor's real documented API max for the `size` pagination parameter
# is 1000 (values above 1000 are silently clamped by LogicMonitor itself);
# use that as the hard cap instead of the SOP's generic 200 fallback.
MAX_PAGE_SIZE = 1000
DEFAULT_PAGE_SIZE = 50

NO_TOKEN = error_envelope(
    "not_configured",
    "No LogicMonitor credentials. Send the X-LogicMonitor-Company, "
    "X-LogicMonitor-Access-Id, and X-LogicMonitor-Access-Key headers.",
    False,
)


def clamp_size(size: int) -> int:
    """Clamp a requested page size to LogicMonitor's real API max (1000)."""
    return max(1, min(size, MAX_PAGE_SIZE))
