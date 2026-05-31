import aiohttp
from .const import API_BASE


class KermiApi:
    def __init__(self, session, token_store):
        self.session = session
        self.token_store = token_store

    async def _headers(self):
        return {
            "Authorization": f"Bearer {await self.token_store.get_access_token()}",
            "Accept": "application/json",
        }

    async def get_favorites(self, installation_id):
        url = f"{API_BASE}/Favorite/GetFavorites/{installation_id}"

        async with self.session.post(url, headers=await self._headers()) as r:
            if r.status == 401:
                await self.token_store.refresh()
                return await self.get_favorites(installation_id)

            return await r.json()