from homeassistant.components.sensor import SensorEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["kermi_xcenter"][entry.entry_id]

    entities = [
        KermiSensor(coordinator, item)
        for item in coordinator.data.get("ResponseData", [])
    ]

    async_add_entities(entities)


class KermiSensor(SensorEntity):
    def __init__(self, coordinator, item):
        self.coordinator = coordinator
        self.item = item

    @property
    def name(self):
        return self.item.get("DisplayName", "Kermi")

    @property
    def unique_id(self):
        return self.item.get("FavoriteId")

    @property
    def native_value(self):
        return self.item.get("DatapointValue", {}).get("Value")

    async def async_update(self):
        await self.coordinator.async_request_refresh()