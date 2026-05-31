import logging

_LOGGER = logging.getLogger(__name__)


class KermiApi:
    def __init__(self, session, auth, base_url):
        self._session = session
        self._auth = auth
        self._base_url = base_url

    async def get_favorites(self, installation_id: str):
        await self._auth.refresh_if_needed()

        url = f"{self._base_url}/xcenterpro/api/Favorite/GetFavorites/{installation_id}"

        async with self._session.get(
            url,
            headers=self._auth.headers(),
            cookies=self._auth.cookies,
        ) as resp:

            if resp.status == 401:
                text = await resp.text()
                _LOGGER.error("401 from API: %s", text)
                raise RuntimeError("Unauthorized")

            if "application/json" not in resp.headers.get("Content-Type", ""):
                text = await resp.text()
                raise RuntimeError(f"Invalid response: {text}")

            return await resp.json()