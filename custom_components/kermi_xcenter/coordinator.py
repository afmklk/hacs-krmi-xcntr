from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .wellknown import HEATPUMP_WELLKNOWN_IDS, extract_wellknown_ids

_LOGGER = logging.getLogger(__name__)

ZERO_DEVICE_ID = "00000000-0000-0000-0000-000000000000"


def _value_type_from_config(config):
    return config.get("$type", "").replace(
        "DatapointConfig`1",
        "DatapointValue`1",
    )


def _normalize_config(config, device_id, wellknown_name=None):
    return {
        "config_id": config.get("DatapointConfigId"),
        "device_id": device_id,
        "type": _value_type_from_config(config),
        "config": {
            **config,
            "WellKnownName": config.get("WellKnownName") or wellknown_name,
        },
        "value": {},
    }


def _normalize_favorite_datapoint(raw):
    config = raw.get("DatapointConfig") or {}
    value = raw.get("DatapointValue") or {}

    config_id = (
        config.get("DatapointConfigId")
        or raw.get("DatapointConfigId")
        or value.get("DatapointConfigId")
    )

    return {
        "config_id": config_id,
        "device_id": value.get("DeviceId") or raw.get("DeviceId"),
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
        self._devices = {}

    async def _discover_devices(self):
        data = await self.api.get_heatpump_devices(self.installation_id)

        for device in data.get("ResponseData", []) or []:
            device_id = device.get("DeviceId")
            if not device_id or device_id == ZERO_DEVICE_ID:
                continue

            self._devices[device_id] = device

        _LOGGER.warning(
            "Kermi device discovery completed: %s devices",
            len(self._devices),
        )

    async def _discover_favorites(self):
        data = await self.api.get_favorites(self.installation_id)

        for item in data.get("ResponseData", []) or []:
            if "FavoriteDatapoint" not in item.get("$type", ""):
                continue

            dp = _normalize_favorite_datapoint(item)
            if dp["config_id"] and dp["device_id"] != ZERO_DEVICE_ID:
                self._datapoints[dp["config_id"]] = dp

    async def _discover_wellknown_heatpump_datapoints(self):
        heatpump_devices = [
            d for d in self._devices.values()
            if d.get("DeviceType") == 2
        ]
    
        if not heatpump_devices:
            _LOGGER.warning("No Kermi heatpump device with DeviceType=2 found")
            return
    
        try:
            js_text = await self.api.get_wellknown_datapoints_js()
            wellknown_ids = extract_wellknown_ids(js_text)
        except Exception:
            _LOGGER.exception("Failed to load dynamic well-known datapoints JS")
            wellknown_ids = {}
    
        if not wellknown_ids:
            wellknown_ids = HEATPUMP_WELLKNOWN_IDS
    
        _LOGGER.warning(
            "Kermi well-known datapoints loaded: %s dynamic, %s fallback",
            len(wellknown_ids),
            len(HEATPUMP_WELLKNOWN_IDS),
        )
    
        for device in heatpump_devices:
            device_id = device["DeviceId"]
            device_type = device["DeviceType"]
            device_version = device.get("SoftwareVersion") or "6.3"
    
            ids = list(dict.fromkeys(wellknown_ids.values()))
    
            data = await self.api.get_configs(
                self.installation_id,
                device_type,
                device_version,
                ids,
            )
    
            configs = data.get("ResponseData", []) or []
    
            reverse_lookup = {
                value.lower(): key
                for key, value in wellknown_ids.items()
            }
    
            _LOGGER.warning(
                "Kermi well-known config discovery for %s: requested=%s returned=%s",
                device.get("Name", device_id),
                len(ids),
                len(configs),
            )
    
            for config in configs:
                config_id = config.get("DatapointConfigId")
                if not config_id:
                    continue
    
                wellknown_name = reverse_lookup.get(config_id.lower())
    
                self._datapoints[config_id] = _normalize_config(
                    config,
                    device_id,
                    wellknown_name=wellknown_name,
                )

    async def _discover(self):
        await self._discover_devices()
        await self._discover_favorites()
        await self._discover_wellknown_heatpump_datapoints()

        self._discovered = True

        _LOGGER.warning(
            "Kermi discovery completed: %s datapoints, %s devices",
            len(self._datapoints),
            len(self._devices),
        )

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
            "devices": self._devices,
        }