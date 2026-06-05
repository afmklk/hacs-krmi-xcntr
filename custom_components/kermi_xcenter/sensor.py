from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity

UNIT_DEVICE_CLASS = {
    "°C": SensorDeviceClass.TEMPERATURE,
    "kW": SensorDeviceClass.POWER,
    "W": SensorDeviceClass.POWER,
    "kWh": SensorDeviceClass.ENERGY,
    "%": SensorDeviceClass.HUMIDITY,
    "bar": SensorDeviceClass.PRESSURE,
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["kermi_xcenter"][entry.entry_id]
    datapoints = coordinator.data.get("datapoints", {})

    entities = []

    for config_id, dp in datapoints.items():
        cfg = dp["config"]

        if cfg.get("Hidden") or cfg.get("Ignore"):
            continue

        entities.append(KermiSensor(coordinator, config_id))

    async_add_entities(entities)


class KermiSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, config_id):
        super().__init__(coordinator)
        self.config_id = config_id

    @property
    def _dp(self):
        return self.coordinator.data["datapoints"][self.config_id]

    @property
    def _cfg(self):
        return self._dp["config"]

    @property
    def name(self):
        return self._cfg.get("DisplayName") or self._cfg.get("WellKnownName") or "Kermi"

    @property
    def unique_id(self):
        return self.config_id

    @property
    def native_unit_of_measurement(self):
        return self._cfg.get("Unit") or None

    @property
    def device_class(self):
        return UNIT_DEVICE_CLASS.get(self.native_unit_of_measurement)

    @property
    def native_value(self):
        raw = self._dp.get("value") or {}
        value = raw.get("Value")

        possible = self._cfg.get("PossibleValues")
        if possible is not None:
            return possible.get(str(value), value)

        return value