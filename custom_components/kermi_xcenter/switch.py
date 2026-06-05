from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "kermi_xcenter"


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    datapoints = coordinator.data.get("datapoints", {})

    entities = []

    for dp in datapoints.values():
        config = dp.get("config", {})
        value = (dp.get("value") or {}).get("Value")

        if config.get("Hidden") or config.get("Ignore"):
            continue

        if not config.get("AllowedInAction"):
            continue

        if config.get("UserLevelWrite", 999) > 10:
            continue

        if not _is_boolean_datapoint(config, value):
            continue

        entities.append(KermiSwitch(coordinator, dp))

    async_add_entities(entities)


class KermiSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, datapoint):
        super().__init__(coordinator)
        self.datapoint = datapoint

        config = datapoint.get("config", {})
        self._attr_name = (
            config.get("DisplayName")
            or config.get("WellKnownName")
            or "Kermi"
        )
        self._attr_unique_id = f"kermi_xcenter_switch_{datapoint['config_id']}"

    @property
    def is_on(self):
        dp = self.coordinator.data["datapoints"].get(
            self.datapoint["config_id"],
            {},
        )
        config = dp.get("config", {})
        value = (dp.get("value") or {}).get("Value")

        if value is None:
            value = config.get("DefaultValue")

        return bool(value)

    async def async_turn_on(self, **kwargs):
        await self.coordinator.api.write_value(
            self.coordinator.installation_id,
            self.datapoint,
            True,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.api.write_value(
            self.coordinator.installation_id,
            self.datapoint,
            False,
        )
        await self.coordinator.async_request_refresh()


def _is_boolean_datapoint(config, value):
    if isinstance(value, bool):
        return True

    if isinstance(config.get("DefaultValue"), bool):
        return True

    possible_values = config.get("PossibleValues") or {}
    possible_keys = {str(key).lower() for key in possible_values.keys()}

    return possible_keys and possible_keys <= {"true", "false"}