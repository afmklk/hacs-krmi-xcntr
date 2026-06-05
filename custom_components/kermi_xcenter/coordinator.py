from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

ZERO_DEVICE_ID = "00000000-0000-0000-0000-000000000000"


def _value_type_from_config(config):
    return config.get("$type", "").replace(
        "DatapointConfig`1",
        "DatapointValue`1",
    )


def _normalize_config(config, device_id=None):
    return {
        "config_id": config.get("DatapointConfigId"),
        "device_id": device_id or config.get("DeviceId"),
        "type": _value_type_from_config(config),
        "config": config,
        "value": {},
    }


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
            update_interval=timedelta(minutes=5),
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
                    "IncludeDatapoints": True,
                    "IncludeChildren": True,
                },
            )
        except Exception:
            _LOGGER.exception("Failed to discover menu %s", menu_id)
            return

        response = data.get("ResponseData") or {}

        device_id = response.get("DeviceId")
        if device_id and device_id != ZERO_DEVICE_ID:
            self._device_ids.add(device_id)

        for bundle in response.get("Bundles", []) or []:
            for raw_dp in bundle.get("Datapoints", []) or []:
                dp = _normalize_datapoint(
                    raw_dp,
                    fallback_device_id=device_id,
                )

                if dp["config_id"]:
                    self._datapoints[dp["config_id"]] = dp

                if dp["device_id"] and dp["device_id"] != ZERO_DEVICE_ID:
                    self._device_ids.add(dp["device_id"])

        for child in response.get("MenuEntries", []) or []:
            child_id = child.get("MenuEntryId")
            if child_id:
                await self._discover_menu(child_id)

    async def _discover_configs_by_filter(self):
        try:
            data = await self.api.get_configs_by_filter(
                self.installation_id,
            )
        except Exception:
            _LOGGER.exception("Failed to discover datapoint configs by filter")
            return

        configs = data.get("ResponseData", []) or []

        _LOGGER.warning(
            "Kermi global config discovery: %s configs",
            len(configs),
        )

        for config in configs:
            config_id = config.get("DatapointConfigId")
            if not config_id:
                continue

            device_id = config.get("DeviceId")
            if device_id and device_id != ZERO_DEVICE_ID:
                self._device_ids.add(device_id)

            existing = self._datapoints.get(config_id)
            if existing:
                existing["config"] = config
                existing["device_id"] = existing.get("device_id") or device_id
                existing["type"] = existing.get("type") or _value_type_from_config(config)
            else:
                self._datapoints[config_id] = _normalize_config(
                    config,
                    device_id=device_id,
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

                if dp["device_id"] and dp["device_id"] != ZERO_DEVICE_ID:
                    self._device_ids.add(dp["device_id"])

                menu_id = dp["config"].get("MenuEntryId")
                if menu_id:
                    menu_ids.add(menu_id)

            elif "FavoriteMenuEntry" in item_type:
                menu_id = item.get("MenuEntryId")
                if menu_id:
                    menu_ids.add(menu_id)

                device_id = item.get("DeviceId")
                if device_id and device_id != ZERO_DEVICE_ID:
                    self._device_ids.add(device_id)

            else:
                device_id = item.get("DeviceId")
                if device_id and device_id != ZERO_DEVICE_ID:
                    self._device_ids.add(device_id)

        for menu_id in menu_ids:
            await self._discover_menu(menu_id)

        await self._discover_configs_by_filter()

        _LOGGER.warning(
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