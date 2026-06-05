from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "kermi_xcenter"


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    datapoints = coordinator.data.get("datapoints", {})

    entities = []

    for dp in datapoints.values():
        config = dp.get("config", {})
        value = dp.get("value", {})

        if not config.get("AllowedInAction"):
            continue

        if config.get("UserLevelWrite", 999) > 10:
            continue

        if value.get("Value") is None:
            continue

        if not isinstance(value.get("Value"), (int, float)):
            continue

        if config.get("PossibleValues"):
            continue

        entities.append(KermiNumber(coordinator, dp))

    async_add_entities(entities)


class KermiNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, datapoint):
        super().__init__(coordinator)
        self.datapoint = datapoint

        config = datapoint.get("config", {})
        self._attr_name = config.get("DisplayName") or config.get("WellKnownName")
        self._attr_unique_id = f"kermi_xcenter_number_{datapoint['config_id']}"

        self._attr_native_min_value = config.get("MinValue")
        self._attr_native_max_value = config.get("MaxValue")
        self._attr_native_step = _step_from_config(config)
        self._attr_native_unit_of_measurement = config.get("Unit") or None

    @property
    def native_value(self):
        dp = self.coordinator.data["datapoints"].get(
            self.datapoint["config_id"],
            {},
        )
        return dp.get("value", {}).get("Value")

    async def async_set_native_value(self, value):
        await self.coordinator.api.write_value(
            self.coordinator.installation_id,
            self.datapoint,
            value,
        )
        await self.coordinator.async_request_refresh()


def _step_from_config(config):
    ui_hint = config.get("UIHint") or ""

    if "Step:0.1" in ui_hint:
        return 0.1

    if "Step:0.5" in ui_hint:
        return 0.5

    if "Step:1" in ui_hint:
        return 1

    if config.get("DatapointType") == 1:
        return 0.1

    return 1