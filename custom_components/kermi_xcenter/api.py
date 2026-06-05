from .const import API_BASE
import logging

_LOGGER = logging.getLogger(__name__)


class KermiApi:
    def __init__(self, session, token_store):
        self.session = session
        self.token_store = token_store

    async def _headers(self):
        return {
            "Authorization": (
                f"Bearer "
                f"{await self.token_store.get_access_token()}"
            ),
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://portal.kermi.com",
            "Referer": "https://portal.kermi.com/",
        }

    
    async def _post(self, url, payload=None):
        headers = await self._headers()
    
        async with self.session.post(
            url,
            headers=headers,
            json=payload,
        ) as r:
    
            text = await r.text()
    
            _LOGGER.warning(
                "Kermi API POST %s -> %s",
                url,
                r.status,
            )
    
            _LOGGER.warning(
                "Kermi API response body: %s",
                text,
            )
    
            if r.status == 401:
                _LOGGER.error(
                    "Access token rejected by Kermi API. Body=%s",
                    text,
                )
    
            r.raise_for_status()
    
            try:
                return await r.json()
            except Exception:
                return text

    async def get_favorites(self, installation_id):
        payload = {
            "WithDetails": True,
            "OnlyHomeScreen": True,
        }
    
        return await self._post(
            f"{API_BASE}/Favorite/GetFavorites/{installation_id}",
            payload,
        )