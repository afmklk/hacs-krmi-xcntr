from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "kermi_xcenter"


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    datapoints = coordinator.data.get("datapoints", {})

    entities = []

    for dp in datapoints.values():
        config = dp.get("config", {})

        if config.get("Hidden") or config.get("Ignore"):
            continue

        possible_values = config.get("PossibleValues") or {}
        if not possible_values:
            continue

        #possible_keys = {str(key).lower() for key in possible_values.keys()}
        #if possible_keys and possible_keys <= {"true", "false", "an", "aus", "on", "off"}:
            #continue
            
        wellknown = config.get("WellKnownName")
        
        possible_keys = {str(key).lower() for key in possible_values.keys()}
        is_boolean_enum = possible_keys and possible_keys <= {"true", "false"}
        
        if is_boolean_enum and wellknown != "System_IsPresent":
            continue

        if not config.get("AllowedInAction"):
            continue

        if config.get("UserLevelWrite", 999) > 10:
            continue

        entities.append(KermiSelect(coordinator, dp))

    async_add_entities(entities)


class KermiSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, datapoint):
        super().__init__(coordinator)
        self.datapoint = datapoint

        config = datapoint.get("config", {})
        self._attr_name = config.get("DisplayName") or config.get("WellKnownName") or "Kermi"
        self._attr_unique_id = f"kermi_xcenter_select_{datapoint['config_id']}"

        self._value_to_option = {}
        self._option_to_value = {}

        for raw_value, label in (config.get("PossibleValues") or {}).items():
            value = _parse_value(raw_value)
            option = str(label)
            self._value_to_option[value] = option
            self._option_to_value[option] = value

        self._attr_options = list(self._option_to_value.keys())

    @property
    def device_info(self):
        device_id = self.datapoint.get("device_id")
        device = self.coordinator.data.get("devices", {}).get(device_id, {})
    
        return {
            "identifiers": {("kermi_xcenter", device_id or "system")},
            "name": device.get("Name") or "Kermi X-Center",
            "manufacturer": "Kermi",
            "model": device.get("Name") or "X-Center",
            "sw_version": device.get("SoftwareVersion"),
            "serial_number": device.get("Serial"),
        }
        
    @property
    def extra_state_attributes(self):
        config = self.datapoint.get("config", {})
        return {
            "description": config.get("Description"),
            "well_known_name": config.get("WellKnownName"),
            "datapoint_config_id": self.datapoint.get("config_id"),
        }

    @property
    def current_option(self):
        dp = self.coordinator.data["datapoints"].get(self.datapoint["config_id"], {})
        value = (dp.get("value") or {}).get("Value")
        return self._value_to_option.get(value)

    async def async_select_option(self, option):
        value = self._option_to_value[option]

        await self.coordinator.api.write_value(
            self.coordinator.installation_id,
            self.datapoint,
            value,
        )
        await self.coordinator.async_request_refresh()


def _parse_value(value):
    text = str(value)

    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False

    try:
        return int(text)
    except ValueError:
        pass

    try:
        return float(text)
    except ValueError:
        return value