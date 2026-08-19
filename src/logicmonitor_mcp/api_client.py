import asyncio
import base64
import hashlib
import hmac
import time
from typing import Any

import httpx

from ._json import error_envelope

_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_MAX_BACKOFF_SECONDS = 20.0

# One shared connection pool for the process lifetime. It carries no auth
# state of its own — company/access_id/access_key are only ever read, per
# request, inside LogicMonitorClient._request() to compute a fresh LMv1
# signature — so sharing it across concurrent tenants is safe (see
# server.py's contextvar-based credential isolation, which is what actually
# keeps tenants apart).
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True)
    return _http_client


# status_code -> (error code, retryable). status_code 0 means a network/
# connection-level failure (no response at all).
_STATUS_TO_CODE: dict[int, tuple[str, bool]] = {
    0: ("upstream_error", True),
    400: ("invalid_argument", False),
    401: ("unauthorized", False),
    403: ("unauthorized", False),
    404: ("not_found", False),
    422: ("invalid_argument", False),
    429: ("rate_limited", True),
}


def _classify(status_code: int) -> tuple[str, bool]:
    if status_code in _STATUS_TO_CODE:
        return _STATUS_TO_CODE[status_code]
    if status_code >= 500:
        return "upstream_error", True
    return "invalid_argument", False


class LogicMonitorError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"LogicMonitor API error {status_code}: {message}")

    def to_envelope(self) -> str:
        code, retryable = _classify(self.status_code)
        return error_envelope(code, self.message, retryable)


def _lmv1_auth_header(
    access_id: str, access_key: str, method: str, resource_path: str, body: str = ""
) -> str:
    """Build the LMv1 Authorization header value.

    Scheme (per LogicMonitor REST API v1/v3 docs): the signature covers the
    HTTP verb, epoch (ms), request body (empty for GET), and the resource
    path (no query string) — HMAC-SHA256 keyed with the Access Key, hex
    digest, then base64-encoded.

    The epoch is embedded in the signed string, so a signature computed for
    one attempt is only valid for a narrow time window. Callers must call
    this again (with a fresh epoch) on every retry attempt rather than
    reusing a previously-computed header — see LogicMonitorClient._request.
    """
    epoch = str(int(time.time() * 1000))
    request_vars = f"{method}{epoch}{body}{resource_path}"
    hex_digest = hmac.new(
        access_key.encode("utf-8"), request_vars.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    signature = base64.b64encode(hex_digest.encode("utf-8")).decode("utf-8")
    return f"LMv1 {access_id}:{signature}:{epoch}"


class LogicMonitorClient:
    """Async httpx client wrapping the LogicMonitor REST API (v3, /santaba/rest).

    Auth is LMv1: a per-request HMAC-SHA256 signature computed from the
    Access Id/Access Key pair, matching how LogicMonitor is configured in
    MSPbots (Company + Access Id + Access Key, no OAuth). This server never
    persists these values — they are supplied per request via headers
    (X-LogicMonitor-Company/-Access-Id/-Access-Key) and used only to sign
    that request. Uses the shared module-level connection pool (see
    _get_http_client) rather than opening a new connection per request.
    """

    def __init__(self, company: str, access_id: str, access_key: str):
        self._base_url = f"https://{company}.logicmonitor.com/santaba/rest"
        self._access_id = access_id
        self._access_key = access_key

    def _clean_params(self, params: dict | None) -> dict:
        if not params:
            return {}
        return {k: v for k, v in params.items() if v is not None}

    async def get(self, path: str, params: dict | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def _request(self, method: str, path: str, params: dict | None = None) -> Any:
        client = _get_http_client()
        target = f"{self._base_url}{path}"
        clean = self._clean_params(params)

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            # LMv1's signature embeds the current epoch, so it must be
            # recomputed on every attempt — reusing an earlier attempt's
            # header would carry a stale timestamp and LogicMonitor would
            # reject it with a 401.
            auth_header = _lmv1_auth_header(self._access_id, self._access_key, method, path)
            headers = {
                "Authorization": auth_header,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            try:
                resp = await client.request(method, target, params=clean, headers=headers)
            except httpx.RequestError as e:
                last_exc = e
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(min(2**attempt, _MAX_BACKOFF_SECONDS))
                    continue
                raise LogicMonitorError(0, f"{e or type(e).__name__} (url={target})") from e

            if resp.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES:
                await asyncio.sleep(self._retry_delay(resp, attempt))
                continue

            self._raise_for_status(resp)
            return self._parse_body(resp)

        # Unreachable in practice (loop always returns or raises above), but
        # keeps type checkers happy and guards against future edits.
        if last_exc:
            raise LogicMonitorError(0, f"{last_exc}") from last_exc
        raise LogicMonitorError(0, "request failed with no response")

    def _retry_delay(self, resp: httpx.Response, attempt: int) -> float:
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), _MAX_BACKOFF_SECONDS)
            except ValueError:
                pass
        return min(2**attempt, _MAX_BACKOFF_SECONDS)

    def _parse_body(self, resp: httpx.Response) -> Any:
        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return {"raw_response": resp.text}

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            try:
                detail = resp.json()
                if isinstance(detail, dict):
                    msg = detail.get("errorMessage") or detail.get("message") or str(detail)
                else:
                    msg = str(detail)
            except ValueError:
                msg = resp.text
            raise LogicMonitorError(resp.status_code, str(msg)[:500])
