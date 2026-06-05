from .const import API_BASE
import logging

_LOGGER = logging.getLogger(__name__)


class KermiApi:
    def __init__(
        self,
        session,
        token_store,
        installation_id,
    ):
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
                    _LOGGER.warning(
                        "Kermi token rejected; refreshing and retrying once"
                    )
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
            {
                "WithDetails": True,
                "OnlyHomeScreen": True,
            },
        )

    async def get_child_entries(
        self,
        installation_id,
        payload,
    ):
        return await self._post(
            f"{API_BASE}/Menu/GetChildEntries/{installation_id}",
            payload,
        )

    async def get_configs_by_device(
        self,
        installation_id,
        device_id,
    ):
        return await self._post(
            f"{API_BASE}/Datapoint/GetConfigsByDeviceId/{installation_id}",
            {
                "DeviceId": device_id,
            },
        )

    async def read_values(
        self,
        installation_id,
        datapoints,
    ):
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

    async def write_value(
        self,
        installation_id,
        datapoint,
        value,
    ):
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