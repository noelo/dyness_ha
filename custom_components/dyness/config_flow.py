"""Config flow for Dyness Battery integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import DynessAPI, DynessAPIError
from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("api_id",     description="API ID"):     str,
        vol.Required("api_secret", description="API Secret"): str,
        vol.Required("sn_bms",     description="Device SN (BMS) — from Dyness portal, e.g. XXXXX-BMS"): str,
        vol.Required("sn_dongle",  description="Dongle SN — from Dyness portal"): str,
        vol.Optional("region", default="global"): vol.In({
            "global": "Global / Europe (open-api.dyness.com)",
            "apac":   "Asia-Pacific (apacopenapi.dyness.com)",
        }),
    }
)


async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    api = DynessAPI(
        api_id     = data["api_id"],
        api_secret = data["api_secret"],
        sn_bms     = data["sn_bms"],
        sn_dongle  = data["sn_dongle"],
        region     = data.get("region", "global"),
    )
    device_info = await api.test_connection()
    model   = device_info.get("deviceModelName") or device_info.get("deviceName") or "Dyness Battery"
    station = device_info.get("stationName") or data["sn_bms"]
    return {"title": f"{model} — {station}"}


class DynessConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except DynessAPIError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input["sn_bms"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
