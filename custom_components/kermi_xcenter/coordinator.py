from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _value_type_from_config(config):
    return config.get("$type", "").replace("DatapointConfig`1", "DatapointValue`1")


def _normalize_datapoint(raw):
    config = raw.get("Config") or raw.get("DatapointConfig") or {}
    value = raw.get("DatapointValue") or {}

    config_id = config.get("DatapointConfigId") or raw.get("DatapointConfigId")
    device_id = value.get("DeviceId") or raw.get("DeviceId")

    return {
        "config_id": config_id,
        "device_id": device_id,
        "type": value.get("$type") or _value_type_from_config(config),
        "config": config,
        "value": value,
    }


class KermiCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, installation_id):
        super().__init__(
            hass,
            logger=_LOGGER,
            name="kermi_xcenter",
            update_interval=timedelta(seconds=30),
        )
        self.api = api
        self.installation_id = installation_id
        self._discovered = False
        self._datapoints = {}

    async def _discover(self):
        favorites = await self.api.get_favorites(self.installation_id)
        items = favorites.get("ResponseData", [])

        menu_ids = set()

        for item in items:
            if "FavoriteDatapoint" in item.get("$type", ""):
                dp = _normalize_datapoint(item)
                if dp["config_id"]:
                    self._datapoints[dp["config_id"]] = dp

                cfg = dp["config"]
                if cfg.get("MenuEntryId"):
                    menu_ids.add(cfg["MenuEntryId"])

            if "FavoriteMenuEntry" in item.get("$type", "") and item.get("MenuEntryId"):
                menu_ids.add(item["MenuEntryId"])

        for menu_id in menu_ids:
            try:
                data = await self.api.get_child_entries(
                    self.installation_id,
                    menu_id,
                )
            except Exception:
                _LOGGER.exception("Failed to discover menu %s", menu_id)
                continue

            response = data.get("ResponseData", {})
            for bundle in response.get("Bundles", []):
                for raw_dp in bundle.get("Datapoints", []):
                    dp = _normalize_datapoint(raw_dp)
                    if dp["config_id"]:
                        self._datapoints[dp["config_id"]] = dp

        self._discovered = True

    async def _async_update_data(self):
        if not self._discovered:
            await self._discover()

        if self._datapoints:
            values = await self.api.read_values(
                self.installation_id,
                list(self._datapoints.values()),
            )

            for raw_value in values.get("ResponseData", []):
                config_id = raw_value.get("DatapointConfigId")
                if config_id in self._datapoints:
                    self._datapoints[config_id]["value"] = raw_value

        return {
            "datapoints": self._datapoints,
        }