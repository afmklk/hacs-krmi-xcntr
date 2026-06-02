from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["kermi_xcenter"][entry.entry_id]
    response = coordinator.data.get("ResponseData", [])
    async_add_entities([KermiSensor(coordinator, item) for item in response])

class KermiSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, item):
        super().__init__(coordinator)
        self.item = item

    @property
    def name(self):
        return self.item.get("DisplayName", "Kermi")

    @property
    def unique_id(self):
        return self.item.get("FavoriteId") or self.item.get("DisplayName")

    @property
    def native_value(self):
        return self.item.get("DatapointValue", {}).get("Value")