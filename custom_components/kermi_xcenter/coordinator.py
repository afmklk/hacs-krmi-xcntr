from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .wellknown import HEATPUMP_WELLKNOWN_IDS, extract_wellknown_ids

_LOGGER = logging.getLogger(__name__)

ZERO_DEVICE_ID = "00000000-0000-0000-0000-000000000000"
SYSTEM_DEVICE_VERSION = "1.5.110.260"


def _normalize_description(text):
    if not text:
        return text

    return (
        str(text)
        .replace("\\n", "\n")
        .replace("\\r", "")
        .strip()
    )


def _normalize_config_dict(config, wellknown_name=None):
    return {
        **config,
        "Description": _normalize_description(config.get("Description")),
        "WellKnownName": config.get("WellKnownName") or wellknown_name,
    }


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
        "config": _normalize_config_dict(
            config,
            wellknown_name=wellknown_name,
        ),
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
        "config": _normalize_config_dict(config),
        "value": value,
    }


def _datapoint_label(dp):
    config = dp.get("config", {})
    return (
        config.get("DisplayName")
        or config.get("WellKnownName")
        or dp.get("config_id")
        or "unknown"
    )


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
        self._config_versions = {}

    async def _discover_devices(self):
        data = await self.api.get_heatpump_devices(self.installation_id)

        for device in data.get("ResponseData", []) or []:
            device_id = device.get("DeviceId")
            if not device_id or device_id == ZERO_DEVICE_ID:
                continue

            self._devices[device_id] = device
            self._config_versions[device_id] = device.get("ConfigVersion")

        self._devices.setdefault(
            ZERO_DEVICE_ID,
            {
                "DeviceId": ZERO_DEVICE_ID,
                "DeviceType": 0,
                "SoftwareVersion": SYSTEM_DEVICE_VERSION,
                "Name": "Kermi X-Center",
                "Serial": None,
                "ConfigVersion": None,
            },
        )

        _LOGGER.info(
            "Kermi device discovery completed: %s devices",
            len(self._devices),
        )

    async def _discover_favorites(self):
        data = await self.api.get_favorites(self.installation_id)

        count_before = len(self._datapoints)

        for item in data.get("ResponseData", []) or []:
            _LOGGER.debug(
                "Kermi favorite found: %s type=%s config=%s device=%s",
                item.get("DisplayName"),
                item.get("$type"),
                item.get("DatapointConfigId"),
                item.get("DeviceId"),
            )

            if "FavoriteDatapoint" not in item.get("$type", ""):
                continue

            dp = _normalize_favorite_datapoint(item)

            if dp["config_id"]:
                self._datapoints[dp["config_id"]] = dp

        _LOGGER.info(
            "Kermi favorite datapoint discovery completed: added=%s total=%s",
            len(self._datapoints) - count_before,
            len(self._datapoints),
        )

    async def _discover_configs_for_device(
        self,
        device,
        wellknown_ids,
        reverse_lookup,
    ):
        device_id = device["DeviceId"]
        device_type = device["DeviceType"]
        device_version = device.get("SoftwareVersion")

        if not device_version:
            device_version = (
                SYSTEM_DEVICE_VERSION
                if device_type == 0
                else "6.3"
            )

        ids = list(dict.fromkeys(wellknown_ids.values()))

        try:
            data = await self.api.get_configs(
                self.installation_id,
                device_type,
                device_version,
                ids,
            )
        except Exception:
            _LOGGER.exception(
                "Kermi config discovery failed for %s device_type=%s version=%s",
                device.get("Name", device_id),
                device_type,
                device_version,
            )
            return

        configs = data.get("ResponseData", []) or []

        _LOGGER.info(
            "Kermi config discovery for %s: device_type=%s version=%s "
            "requested=%s returned=%s",
            device.get("Name", device_id),
            device_type,
            device_version,
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

    async def _discover_wellknown_heatpump_datapoints(self):
        try:
            js_text = await self.api.get_wellknown_datapoints_js()
            dynamic_ids = extract_wellknown_ids(js_text)
        except Exception:
            _LOGGER.exception("Failed to load dynamic well-known datapoints JS")
            dynamic_ids = {}

        wellknown_ids = {
            **HEATPUMP_WELLKNOWN_IDS,
            **dynamic_ids,
        }

        reverse_lookup = {
            value.lower(): key
            for key, value in wellknown_ids.items()
        }

        _LOGGER.info(
            "Kermi well-known datapoints loaded: static=%s dynamic=%s merged=%s",
            len(HEATPUMP_WELLKNOWN_IDS),
            len(dynamic_ids),
            len(wellknown_ids),
        )

        for device in self._devices.values():
            if device.get("DeviceType") not in (0, 2):
                continue

            await self._discover_configs_for_device(
                device=device,
                wellknown_ids=wellknown_ids,
                reverse_lookup=reverse_lookup,
            )

    async def _check_config_version_changes(self):
        data = await self.api.get_heatpump_devices(self.installation_id)

        changed = False

        for device in data.get("ResponseData", []) or []:
            device_id = device.get("DeviceId")
            if not device_id or device_id == ZERO_DEVICE_ID:
                continue

            new_version = device.get("ConfigVersion")
            old_version = self._config_versions.get(device_id)

            if (
                old_version is not None
                and new_version is not None
                and new_version != old_version
            ):
                _LOGGER.info(
                    "Kermi ConfigVersion changed for %s: %s -> %s",
                    device.get("Name", device_id),
                    old_version,
                    new_version,
                )
                changed = True

            self._config_versions[device_id] = new_version
            self._devices[device_id] = device

        return changed

    def _log_discovered_datapoints(self):
        sensor_count = 0
        number_count = 0
        select_count = 0
        switch_count = 0
        writable_count = 0

        for dp in self._datapoints.values():
            config = dp.get("config", {})
            value = dp.get("value", {})
            native_value = value.get("Value")
            possible_values = config.get("PossibleValues")

            is_writable = (
                bool(config.get("AllowedInAction"))
                and config.get("UserLevelWrite", 999) <= 10
            )

            if is_writable:
                writable_count += 1

            possible_keys = {
                str(key).lower()
                for key in (possible_values or {}).keys()
            }
            is_boolean_enum = (
                possible_keys
                and possible_keys <= {"true", "false"}
            )

            if possible_values and not is_boolean_enum:
                select_count += 1
            elif is_boolean_enum or isinstance(native_value, bool):
                switch_count += 1
            elif isinstance(native_value, (int, float)) and is_writable:
                number_count += 1
            else:
                sensor_count += 1

            _LOGGER.debug(
                "Kermi DP: name=%s config_id=%s device_id=%s type=%s unit=%s "
                "value=%s writable=%s possible_values=%s min=%s max=%s ui_hint=%s",
                _datapoint_label(dp),
                dp.get("config_id"),
                dp.get("device_id"),
                dp.get("type"),
                config.get("Unit"),
                native_value,
                is_writable,
                bool(possible_values),
                config.get("MinValue"),
                config.get("MaxValue"),
                config.get("UIHint"),
            )

        _LOGGER.info(
            "Kermi datapoint classification: sensors=%s numbers=%s selects=%s "
            "switches=%s writable=%s total=%s",
            sensor_count,
            number_count,
            select_count,
            switch_count,
            writable_count,
            len(self._datapoints),
        )

    async def _rediscover(self):
        _LOGGER.info("Kermi configuration change detected, running rediscovery")

        self._datapoints.clear()
        self._devices.clear()
        self._config_versions.clear()
        self._discovered = False

        await self._discover()

    async def _discover(self):
        await self._discover_devices()
        await self._discover_favorites()
        await self._discover_wellknown_heatpump_datapoints()

        _LOGGER.info(
            "Kermi discovery completed: %s datapoints, %s devices",
            len(self._datapoints),
            len(self._devices),
        )

        self._log_discovered_datapoints()

        self._discovered = True

    async def _async_update_data(self):
        if not self._discovered:
            await self._discover()
        else:
            try:
                if await self._check_config_version_changes():
                    await self._rediscover()
            except Exception:
                _LOGGER.exception("Failed checking Kermi ConfigVersion")

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