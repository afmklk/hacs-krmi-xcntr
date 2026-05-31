from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


class KermiCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client, installation_id):
        super().__init__(
            hass,
            logger=None,
            name="Kermi X-Center",
            update_interval=timedelta(seconds=300),
        )
        self.client = client
        self.installation_id = installation_id

    async def _async_update_data(self):
        return await self.client.get_favorites(self.installation_id)