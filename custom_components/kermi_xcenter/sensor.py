from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "kermi_xcenter"

UNIT_DEVICE_CLASS = {
    "°C": SensorDeviceClass.TEMPERATURE,
    "kW": SensorDeviceClass.POWER,
    "W": SensorDeviceClass.POWER,
    "kWh": SensorDeviceClass.ENERGY,
    "%": SensorDeviceClass.HUMIDITY,
    "bar": SensorDeviceClass.PRESSURE,
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    datapoints = coordinator.data.get("datapoints", {})

    entities = []

    for config_id, dp in datapoints.items():
        cfg = dp.get("config", {})
        value = (dp.get("value") or {}).get("Value")

        if cfg.get("Hidden") or cfg.get("Ignore"):
            continue

        # Exposed as select.py
        is_writable = (
            cfg.get("AllowedInAction")
            and cfg.get("UserLevelWrite", 999) <= 10
        )
        
        if cfg.get("PossibleValues") and is_writable:
            continue

        # Exposed as switch.py
        if (
            cfg.get("AllowedInAction")
            and cfg.get("UserLevelWrite", 999) <= 10
            and isinstance(value, bool)
        ):
            continue

        # Exposed as number.py
        if (
            cfg.get("AllowedInAction")
            and cfg.get("UserLevelWrite", 999) <= 10
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
        ):
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
        return (
            self._cfg.get("DisplayName")
            or self._cfg.get("WellKnownName")
            or "Kermi"
        )

    @property
    def unique_id(self):
        return f"kermi_xcenter_sensor_{self.config_id}"

    @property
    def extra_state_attributes(self):
        config = self._cfg  # sensor.py
        return {
            "description": config.get("Description"),
            "well_known_name": config.get("WellKnownName"),
            "datapoint_config_id": self.config_id,
        }

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
    
        possible = self._cfg.get("PossibleValues") or {}
        if possible:
            return possible.get(str(value), value)
    
        return value
        
    @property
    def device_info(self):
        device_id = self._dp.get("device_id")
        device = self.coordinator.data.get("devices", {}).get(device_id, {})
    
        return {
            "identifiers": {("kermi_xcenter", device_id or "system")},
            "name": device.get("Name") or "Kermi X-Center",
            "manufacturer": "Kermi",
            "model": device.get("Name") or "X-Center",
            "sw_version": device.get("SoftwareVersion"),
            "serial_number": device.get("Serial"),
        }