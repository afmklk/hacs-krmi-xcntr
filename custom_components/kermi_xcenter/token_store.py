import logging
import time

_LOGGER = logging.getLogger(__name__)


class TokenStore:
    def __init__(self, token_client, update_callback=None):
        self.client = token_client
        self.update_callback = update_callback

        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0

    async def set_initial(self, token_data):
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token")
        self.expires_at = time.time() + token_data.get("expires_in", 3600)

    async def get_access_token(self):
        if not self.access_token:
            raise ValueError("No access token available")

        # Refresh 5 minutes before expiry
        if self.refresh_token and time.time() >= self.expires_at - 300:
            await self.refresh()

        return self.access_token

    async def refresh(self):
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        data = await self.client.refresh(self.refresh_token)

        if "access_token" not in data:
            raise ValueError(f"Token refresh failed: {data}")

        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        self.expires_at = time.time() + data.get("expires_in", 3600)

        if self.update_callback:
            self.update_callback(data)