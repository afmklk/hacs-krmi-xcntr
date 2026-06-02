import time


class TokenStore:
    def __init__(self, token_client):
        self.client = token_client

        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0

    async def set_initial(self, token_data):
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]
        self.expires_at = time.time() + token_data["expires_in"]

    async def get_access_token(self):
        if time.time() >= self.expires_at:
            await self.refresh()
        return self.access_token

    async def refresh(self):
        data = await self.client.refresh(self.refresh_token)

        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        self.expires_at = time.time() + data["expires_in"]