from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class KermiCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, installation_id):
        super().__init__(
            hass,
            logger=_LOGGER,
            name="kermi_xcenter",
            update_interval=timedelta(seconds=30),
        )
        self.api = api
        self.installation_id = installation_id

    async def _async_update_data(self):
        data = await self.api.get_favorites(self.installation_id)
        return data or {}