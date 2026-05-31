import aiohttp
from .const import TOKEN_URL


class TokenClient:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def exchange_code(self, code, redirect_uri, verifier):
        async with self.session.post(
            TOKEN_URL,
            data={
                "client_id": "XCenterUI",
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": verifier,
            },
        ) as r:
            return await r.json()

    async def refresh(self, refresh_token):
        async with self.session.post(
            TOKEN_URL,
            data={
                "client_id": "XCenterUI",
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        ) as r:
            return await r.json()