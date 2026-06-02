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

    async def _post(self, url, payload=None):
        async with self.session.post(url, headers=await self._headers(), json=payload) as r:
            if r.status == 401:
                await self.token_store.refresh()
                return await self._post(url, payload)
            r.raise_for_status()
            return await r.json()

    async def get_favorites(self, installation_id):
        return await self._post(f"{API_BASE}/Favorite/GetFavorites/{installation_id}")