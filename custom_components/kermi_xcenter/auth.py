import time
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


class KermiAuth:
    def __init__(self, session: aiohttp.ClientSession, base_url: str):
        self._session = session
        self._base_url = base_url

        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0

        self.cookies = {}

    def set_tokens(self, data: dict):
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token")
        self.expires_at = time.time() + int(data.get("expires_in", 3600))

    async def refresh_if_needed(self):
        if time.time() < self.expires_at - 30:
            return

        if not self.refresh_token:
            raise RuntimeError("No refresh token")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": "XCenterUI",
        }

        async with self._session.post(
            f"{self._base_url}/openid/connect/token",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:

            data = await resp.json()
            self.set_tokens(data)

    def headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }