import logging

import aiohttp

from .const import TOKEN_URL

_LOGGER = logging.getLogger(__name__)


class TokenClient:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def exchange_code(self, code, redirect_uri, verifier):
        payload = {
            "client_id": "XCenterUI",
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        }

        async with self.session.post(
            TOKEN_URL,
            data=payload,
        ) as response:
            body = await response.text()

            _LOGGER.debug(
                "Kermi token exchange status=%s body=%s",
                response.status,
                body,
            )

            try:
                data = await response.json()
            except Exception as err:
                raise ValueError(
                    f"Failed to parse token exchange response: {body}"
                ) from err

            if response.status >= 400:
                raise ValueError(
                    f"Token exchange failed: HTTP {response.status}, "
                    f"response={data}"
                )

            return data

    async def refresh(self, refresh_token):
        payload = {
            "client_id": "XCenterUI",
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        async with self.session.post(
            TOKEN_URL,
            data=payload,
        ) as response:
            body = await response.text()

            _LOGGER.warning(
                "Kermi refresh status=%s body=%s",
                response.status,
                body,
            )

            try:
                data = await response.json()
            except Exception as err:
                raise ValueError(
                    f"Failed to parse refresh response: {body}"
                ) from err

            if response.status >= 400:
                raise ValueError(
                    f"Token refresh failed: HTTP {response.status}, "
                    f"response={data}"
                )

            return data