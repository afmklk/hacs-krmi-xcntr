import asyncio
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

        self._refresh_lock = asyncio.Lock()
        self._refresh_failed = False

    async def set_initial(self, token_data):
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token")

        expires_in = token_data.get("expires_in", 3600)
        self.expires_at = time.time() + expires_in

        self._refresh_failed = False

    async def get_access_token(self):
        if not self.access_token:
            raise ValueError("No access token available")

        if self._refresh_failed:
            raise ValueError(
                "Kermi token refresh previously failed. "
                "Please reconfigure the integration with fresh browser tokens."
            )

        if self.refresh_token and time.time() >= self.expires_at - 300:
            await self.refresh()

        return self.access_token

    async def refresh(self, force=False):
        async with self._refresh_lock:
            now = time.time()

            if self._refresh_failed:
                raise ValueError(
                    "Kermi token refresh previously failed. "
                    "Please reconfigure the integration with fresh browser tokens."
                )

            # Another coroutine may already have refreshed while we waited.
            if (
                not force
                and self.access_token
                and now < self.expires_at - 300
            ):
                return

            if not self.refresh_token:
                self._refresh_failed = True
                raise ValueError("No refresh token available")

            old_refresh_token = self.refresh_token

            try:
                data = await self.client.refresh(old_refresh_token)
            except Exception:
                self._refresh_failed = True
                raise

            new_access_token = data.get("access_token")
            new_refresh_token = data.get("refresh_token")
            expires_in = data.get("expires_in", 3600)

            if not new_access_token:
                self._refresh_failed = True
                raise ValueError(f"Refresh response missing access_token: {data}")

            if not new_refresh_token:
                # Kermi/OpenIddict appears to rotate refresh tokens.
                # If no new refresh token is returned, keeping the old one may cause
                # 'already redeemed' or 'no longer valid' on the next refresh.
                _LOGGER.warning(
                    "Kermi refresh response did not include a new refresh token"
                )
                new_refresh_token = old_refresh_token

            self.access_token = new_access_token
            self.refresh_token = new_refresh_token
            self.expires_at = time.time() + expires_in
            self._refresh_failed = False

            if self.update_callback:
                self.update_callback(
                    {
                        "access_token": self.access_token,
                        "refresh_token": self.refresh_token,
                        "expires_in": expires_in,
                    }
                )

            _LOGGER.debug("Kermi token refreshed and persisted")
