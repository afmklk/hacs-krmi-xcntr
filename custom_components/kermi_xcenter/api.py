import logging

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class KermiApi:
    def __init__(self, session, token_store, installation_id):
        self.session = session
        self.token_store = token_store
        self.installation_id = installation_id

    async def _headers(self):
        token = await self.token_store.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
        }

    async def _post(self, url, payload=None):
        if payload is None:
            payload = {}

        for attempt in range(2):
            async with self.session.post(
                url,
                headers=await self._headers(),
                json=payload,
            ) as r:
                text = await r.text()

                _LOGGER.debug(
                    "Kermi API POST %s -> %s body=%s",
                    url,
                    r.status,
                    text[:1000],
                )

                if r.status == 401 and attempt == 0:
                    await self.token_store.refresh()
                    continue

                r.raise_for_status()

                try:
                    return await r.json()
                except Exception:
                    return text

    async def get_favorites(self, installation_id):
        return await self._post(
            f"{API_BASE}/Favorite/GetFavorites/{installation_id}",
            {"WithDetails": True, "OnlyHomeScreen": True},
        )

    async def get_all_devices(self, installation_id):
        return await self._post(
            f"{API_BASE}/Device/GetAllDevices/{installation_id}",
            {},
        )

    async def get_configs(self, installation_id, device_type, device_version, config_ids):
        return await self._post(
            f"{API_BASE}/Datapoint/GetConfigs/{installation_id}",
            {
                "DeviceType": device_type,
                "DeviceVersion": device_version,
                "DatapointConfigIds": config_ids,
                "IgnoreNotExisting": True,
            },
        )

    async def read_values(self, installation_id, datapoints):
        return await self._post(
            f"{API_BASE}/Datapoint/ReadValues/{installation_id}",
            {
                "DatapointValues": [
                    {
                        "$type": dp["type"],
                        "DatapointConfigId": dp["config_id"],
                        "DeviceId": dp["device_id"],
                    }
                    for dp in datapoints
                ]
            },
        )

    async def write_value(self, installation_id, datapoint, value):
        return await self._post(
            f"{API_BASE}/Datapoint/WriteValues/{installation_id}",
            {
                "DatapointValues": [
                    {
                        "$type": datapoint["type"],
                        "DatapointConfigId": datapoint["config_id"],
                        "DeviceId": datapoint["device_id"],
                        "Flags": 0,
                        "Value": value,
                    }
                ]
            },
        )