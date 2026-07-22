import base64
import hashlib
import hmac
import time
from typing import Any

import httpx


class LogicMonitorError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"LogicMonitor API error {status_code}: {message}")


def _lmv1_auth_header(access_id: str, access_key: str, method: str, resource_path: str, body: str = "") -> str:
    """Build the LMv1 Authorization header value.

    Scheme (per LogicMonitor REST API v1/v3 docs): the signature covers the
    HTTP verb, epoch (ms), request body (empty for GET), and the resource
    path (no query string) — HMAC-SHA256 keyed with the Access Key, hex
    digest, then base64-encoded.
    """
    epoch = str(int(time.time() * 1000))
    request_vars = f"{method}{epoch}{body}{resource_path}"
    hex_digest = hmac.new(access_key.encode("utf-8"), request_vars.encode("utf-8"), hashlib.sha256).hexdigest()
    signature = base64.b64encode(hex_digest.encode("utf-8")).decode("utf-8")
    return f"LMv1 {access_id}:{signature}:{epoch}"


class LogicMonitorClient:
    """Async httpx client wrapping the LogicMonitor REST API (v3, /santaba/rest).

    Auth is LMv1: a per-request HMAC-SHA256 signature computed from the
    Access Id/Access Key pair, matching how LogicMonitor is configured in
    MSPbots (Company + Access Id + Access Key, no OAuth). This server never
    persists these values — they are supplied per request via headers
    (X-LogicMonitor-Company/-Access-Id/-Access-Key) and used only to sign
    that request.
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
        clean = self._clean_params(params)
        target = f"{self._base_url}{path}"
        auth_header = _lmv1_auth_header(self._access_id, self._access_key, "GET", path)
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(target, params=clean, headers=headers)
        except httpx.RequestError as e:
            raise LogicMonitorError(0, f"Could not reach {target!r}: {e or type(e).__name__}") from None

        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except ValueError:
                detail = resp.text
            raise LogicMonitorError(resp.status_code, str(detail)[:500])

        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return {"raw_response": resp.text}
