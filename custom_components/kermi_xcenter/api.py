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
    
        _LOGGER.warning(
            "Using access token prefix: %s",
            token[:80],
        )
    
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://portal.kermi.com",
            "Referer": (
                f"https://portal.kermi.com/XCenterUI/"
                f"RemoteControlNew/de/DE/"
                f"{self.installation_id}/homescreen"
            ),
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
            "Kermi API POST %s -> %s body=%s",
            url,
            r.status,
            text[:1000],
            )
    
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