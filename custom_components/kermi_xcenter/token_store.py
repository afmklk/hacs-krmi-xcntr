import logging
import time

_LOGGER = logging.getLogger(__name__)


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

        _LOGGER.debug(
            "Initial token stored, expires in %s seconds",
            token_data["expires_in"],
        )

    async def get_access_token(self):
        if not self.access_token:
        	raise ValueError("No access token available")
	
        if (
			self.refresh_token
			and time.time() >= self.expires_at
        ):
        	await self.refresh()
	
        return self.access_token

    async def refresh(self):
        if not self.refresh_token:
            raise ValueError(
                "No refresh token available"
            )

        data = await self.client.refresh(
            self.refresh_token
        )

        _LOGGER.warning(
            "Kermi refresh response: %s",
            data,
        )

        if "access_token" not in data:
            raise ValueError(
                "Refresh response missing access_token. "
                f"Response={data}"
            )

        self.access_token = data["access_token"]

        self.refresh_token = data.get(
            "refresh_token",
            self.refresh_token,
        )

        expires_in = data.get("expires_in")

        if expires_in is None:
            raise ValueError(
                "Refresh response missing expires_in. "
                f"Response={data}"
            )

        self.expires_at = time.time() + expires_in

        _LOGGER.debug(
            "Token refreshed successfully, expires in %s seconds",
            expires_in,
        )