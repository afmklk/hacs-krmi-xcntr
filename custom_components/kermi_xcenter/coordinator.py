from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _value_type_from_config(config):
    return config.get("$type", "").replace(
        "DatapointConfig`1",
        "DatapointValue`1",
    )


def _normalize_datapoint(raw, fallback_device_id=None):
    config = raw.get("Config") or raw.get("DatapointConfig") or {}
    value = raw.get("DatapointValue") or {}

    config_id = (
        config.get("DatapointConfigId")
        or raw.get("DatapointConfigId")
        or value.get("DatapointConfigId")
    )

    device_id = (
        value.get("DeviceId")
        or raw.get("DeviceId")
        or fallback_device_id
    )

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
        self._visited_menu_ids = set()
        self._device_ids = set()

    async def _discover_menu(self, menu_id):
        if not menu_id or menu_id in self._visited_menu_ids:
            return

        self._visited_menu_ids.add(menu_id)

        try:
            data = await self.api.get_child_entries(
                self.installation_id,
                {
                    "MenuEntryId": menu_id,
                    "WithDetails": True,
                },
            )
        except Exception:
            _LOGGER.exception("Failed to discover menu %s", menu_id)
            return

        response = data.get("ResponseData") or {}

        device_id = response.get("DeviceId")
        if device_id:
            self._device_ids.add(device_id)

        for bundle in response.get("Bundles", []) or []:
            for raw_dp in bundle.get("Datapoints", []) or []:
                dp = _normalize_datapoint(
                    raw_dp,
                    fallback_device_id=device_id,
                )

                if dp["config_id"]:
                    self._datapoints[dp["config_id"]] = dp

                if dp["device_id"]:
                    self._device_ids.add(dp["device_id"])

        for child in response.get("MenuEntries", []) or []:
            child_id = child.get("MenuEntryId")
            if child_id:
                await self._discover_menu(child_id)

    async def _discover_device_configs(self):
        for device_id in list(self._device_ids):
            try:
                data = await self.api.get_configs_by_device(
                    self.installation_id,
                    device_id,
                )
            except Exception:
                _LOGGER.exception(
                    "Failed to discover datapoint configs for device %s",
                    device_id,
                )
                continue

            for config in data.get("ResponseData", []) or []:
                config_id = config.get("DatapointConfigId")

                if not config_id:
                    continue

                if config_id not in self._datapoints:
                    self._datapoints[config_id] = {
                        "config_id": config_id,
                        "device_id": device_id,
                        "type": _value_type_from_config(config),
                        "config": config,
                        "value": {},
                    }
                else:
                    self._datapoints[config_id]["config"] = config
                    self._datapoints[config_id]["device_id"] = (
                        self._datapoints[config_id].get("device_id")
                        or device_id
                    )
                    self._datapoints[config_id]["type"] = (
                        self._datapoints[config_id].get("type")
                        or _value_type_from_config(config)
                    )

    async def _discover(self):
        favorites = await self.api.get_favorites(self.installation_id)
        items = favorites.get("ResponseData", []) or []

        menu_ids = set()

        for item in items:
            item_type = item.get("$type", "")

            if "FavoriteDatapoint" in item_type:
                dp = _normalize_datapoint(item)

                if dp["config_id"]:
                    self._datapoints[dp["config_id"]] = dp

                if dp["device_id"]:
                    self._device_ids.add(dp["device_id"])

                menu_id = dp["config"].get("MenuEntryId")
                if menu_id:
                    menu_ids.add(menu_id)

            elif "FavoriteMenuEntry" in item_type:
                menu_id = item.get("MenuEntryId")
                if menu_id:
                    menu_ids.add(menu_id)

                device_id = item.get("DeviceId")
                if device_id:
                    self._device_ids.add(device_id)

            else:
                device_id = item.get("DeviceId")
                if device_id and device_id != "00000000-0000-0000-0000-000000000000":
                    self._device_ids.add(device_id)

        for menu_id in menu_ids:
            await self._discover_menu(menu_id)

        await self._discover_device_configs()

        _LOGGER.info(
            "Kermi discovery completed: %s datapoints, %s devices, %s menus",
            len(self._datapoints),
            len(self._device_ids),
            len(self._visited_menu_ids),
        )

        self._discovered = True

    async def _async_update_data(self):
        if not self._discovered:
            await self._discover()

        if self._datapoints:
            values = await self.api.read_values(
                self.installation_id,
                list(self._datapoints.values()),
            )

            for raw_value in values.get("ResponseData", []) or []:
                config_id = raw_value.get("DatapointConfigId")
                if config_id in self._datapoints:
                    self._datapoints[config_id]["value"] = raw_value

        return {
            "datapoints": self._datapoints,
            "devices": sorted(self._device_ids),
            "menus": sorted(self._visited_menu_ids),
        }