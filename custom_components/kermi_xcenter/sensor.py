from homeassistant.helpers.entity import Entity


def slugify(name):
    return name.lower().replace("_", ".")


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data

    entities = []

    for item in coordinator.data.get("ResponseData", []):
        config = item.get("DatapointConfig", {})
        value = item.get("DatapointValue", {})

        key = config.get("WellKnownName")
        if not key:
            continue

        entities.append(KermiSensor(coordinator, key, config))

    async_add_entities(entities)


class KermiSensor(Entity):
    def __init__(self, coordinator, key, config):
        self.coordinator = coordinator
        self.key = key
        self.config = config

    @property
    def name(self):
        return self.config.get("DisplayName", self.key)

    @property
    def unique_id(self):
        return f"kermi_{self.key}"

    @property
    def state(self):
        data = self.coordinator.data.get("ResponseData", [])

        for item in data:
            if item.get("DatapointConfig", {}).get("WellKnownName") == self.key:
                return item.get("DatapointValue", {}).get("Value")

        return None

    @property
    def unit_of_measurement(self):
        return self.config.get("Unit")