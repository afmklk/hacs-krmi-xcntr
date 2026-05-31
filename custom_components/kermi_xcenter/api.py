import aiohttp
from .const import TOKEN_URL, API_BASE


class KermiApiClient:
    def __init__(self, session, access_token, refresh_token):
        self.session = session
        self.access_token = access_token
        self.refresh_token = refresh_token

    async def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    async def refresh_token_flow(self, client_id):
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": client_id,
        }

        async with self.session.post(TOKEN_URL, data=data) as r:
            data = await r.json()
            self.access_token = data["access_token"]
            self.refresh_token = data.get("refresh_token", self.refresh_token)

    async def get_favorites(self, installation_id):
        url = f"{API_BASE}/Favorite/GetFavorites/{installation_id}"

        async with self.session.post(
            url,
            headers=await self._headers(),
            json={}
        ) as r:
            return await r.json()