"""Dyness API client."""
import hashlib
import hmac
import base64
import json
import logging
from datetime import datetime, timezone

import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE_URLS = {
    "global": "https://open-api.dyness.com/openapi/ems-device",
    "apac":   "https://apacopenapi.dyness.com/openapi/ems-device",
}


class DynessAPIError(Exception):
    """Raised when the API returns an error."""


class DynessAPI:
    """Async Dyness API client — works with any Dyness product."""

    def __init__(self, api_id: str, api_secret: str, sn_bms: str, sn_dongle: str,
                 sn_module: str = "", region: str = "global"):
        self.api_id     = api_id
        self.api_secret = api_secret
        self.sn_bms     = sn_bms
        self.sn_dongle  = sn_dongle
        self.sn_module  = sn_module
        self.base_url   = BASE_URLS.get(region, BASE_URLS["global"])

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _gmt_time(self) -> str:
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    def _md5(self, body: str) -> str:
        return base64.b64encode(hashlib.md5(body.encode("utf-8")).digest()).decode("utf-8")

    def _sign(self, method: str, md5: str, content_type: str, date: str, path: str) -> str:
        sts = f"{method}\n{md5}\n{content_type}\n{date}\n{path}"
        raw = hmac.new(self.api_secret.encode("utf-8"), sts.encode("utf-8"), hashlib.sha1).digest()
        return base64.b64encode(raw).decode("utf-8")

    def _headers(self, path: str, body_str: str) -> dict:
        md5  = self._md5(body_str)
        date = self._gmt_time()
        sig  = self._sign("POST", md5, "application/json", date, path)
        return {
            "Content-Type":  "application/json;charset=UTF-8",
            "Content-MD5":   md5,
            "Date":          date,
            "Authorization": f"API {self.api_id}:{sig}",
        }

    async def _post(self, session: aiohttp.ClientSession, path: str, body: dict) -> dict:
        body_str = json.dumps(body, separators=(",", ":"))
        headers  = self._headers(path, body_str)
        url      = self.base_url + path
        try:
            async with session.post(
                url, headers=headers, data=body_str,
                ssl=False, timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                data = await resp.json(content_type=None)
                if str(data.get("code")) not in ("0", "200"):
                    raise DynessAPIError(
                        f"{path} → code={data.get('code')} | {data.get('info')}"
                    )
                return data
        except DynessAPIError:
            raise
        except Exception as err:
            raise DynessAPIError(f"Request to {path} failed: {err}") from err

    # ── Public methods ────────────────────────────────────────────────────────

    async def test_connection(self) -> dict:
        """Verify credentials. Returns device info dict on success."""
        async with aiohttp.ClientSession() as session:
            r = await self._post(
                session,
                "/v1/device/household/storage/detail",
                {"deviceSn": self.sn_bms}
            )
        return r.get("data", {})

    async def get_all_data(self) -> dict:
        """Fetch all available data and return a unified dict."""
        result = {}

        async with aiohttp.ClientSession() as session:

            # 1. Device info (model, firmware, communication status, etc.)
            try:
                r = await self._post(
                    session,
                    "/v1/device/household/storage/detail",
                    {"deviceSn": self.sn_bms}
                )
                result["device"] = r.get("data", {})
            except DynessAPIError as e:
                _LOGGER.warning("Device detail failed: %s", e)
                result["device"] = {}

            # 2. Power / SOC history — take the latest non-null entry
            try:
                r = await self._post(
                    session,
                    "/v1/device/getLastPowerDataBySn",
                    {"deviceSn": self.sn_bms}
                )
                records = [
                    x for x in (r.get("data") or [])
                    if x.get("realTimePower") is not None
                ]
                result["power"] = records[-1] if records else {}
            except DynessAPIError as e:
                _LOGGER.warning("Power data failed: %s", e)
                result["power"] = {}

            # 3. BMS real-time points (cell voltages, temps, alarms, etc.)
            try:
                r = await self._post(
                    session,
                    "/v1/device/realTime/data",
                    {"deviceSn": self.sn_bms}
                )
                result["bms"] = {
                    p["pointId"]: p["pointValue"]
                    for p in (r.get("data") or [])
                }
                # Auto-discover module SN from SUB field
                if not self.sn_module:
                    sub = result["bms"].get("SUB", "")
                    modules = [s.strip() for s in sub.split(",") if s.strip()]
                    if modules:
                        self.sn_module = modules[0]
                        _LOGGER.debug("Auto-discovered module SN: %s", self.sn_module)
            except DynessAPIError as e:
                _LOGGER.warning("BMS real-time data failed: %s", e)
                result["bms"] = {}

            # 4. Dongle/data-logger diagnostics (signal strength, uptime, etc.)
            try:
                r = await self._post(
                    session,
                    "/v1/device/realTime/data",
                    {"deviceSn": self.sn_dongle}
                )
                result["dongle"] = {
                    p["pointId"]: p["pointValue"]
                    for p in (r.get("data") or [])
                }
            except DynessAPIError as e:
                _LOGGER.warning("Dongle data failed: %s", e)
                result["dongle"] = {}

        return result
