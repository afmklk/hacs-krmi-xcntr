from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import logging

_LOGGER = logging.getLogger(__name__)


class KermiCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, installation_id: str):
        super().__init__(
            hass,
            logger=_LOGGER,
            name="kermi_xcenter",
            update_interval=timedelta(seconds=60),
        )

        self.api = api
        self.installation_id = installation_id

    async def _async_update_data(self):
        try:
            return await self.api.get_favorites(self.installation_id)
        except Exception as e:
            raise UpdateFailed(str(e))