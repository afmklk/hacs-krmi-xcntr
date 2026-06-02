from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

class KermiCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, installation_id):
        super().__init__(
            hass,
            logger=__name__,
            name="kermi_xcenter",
            update_interval=timedelta(seconds=30),
        )
        self.api = api
        self.installation_id = installation_id

    async def _async_update_data(self):
        data = await self.api.get_favorites(self.installation_id)
        return data or {}