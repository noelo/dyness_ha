"""Dyness data update coordinator."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DynessAPI, DynessAPIError

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


class DynessCoordinator(DataUpdateCoordinator):
    """Coordinator that fetches all Dyness data every 5 minutes."""

    def __init__(self, hass: HomeAssistant, api: DynessAPI) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Dyness Battery",
            update_interval=SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> dict:
        try:
            return await self.api.get_all_data()
        except DynessAPIError as err:
            raise UpdateFailed(f"Dyness API error: {err}") from err
