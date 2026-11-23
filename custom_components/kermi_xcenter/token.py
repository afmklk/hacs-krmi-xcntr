import logging

import aiohttp

from .const import DEFAULT_PORTAL, PORTALS
_LOGGER = logging.getLogger(__name__)


class TokenClient:
    def __init__(self, session: aiohttp.ClientSession, portal=DEFAULT_PORTAL):
        self.session = session
        self.portal = PORTALS.get(portal, PORTALS[DEFAULT_PORTAL])

    async def exchange_code(self, code, verifier):
        async with self.session.post(
            self.portal["token_url"],
            data={
                "client_id": self.portal["client_id"],
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.portal["redirect_uri"],
                "code_verifier": verifier,
            },
        ) as r:
            data = await r.json(content_type=None)

            if r.status >= 400:
                _LOGGER.error(
                    "Kermi token exchange failed: HTTP %s response=%s",
                    r.status,
                    _redact(data),
                )
                raise ValueError(
                    f"Token exchange failed: HTTP {r.status}, response={data}"
                )

            return data

    async def refresh(self, refresh_token):
        async with self.session.post(
            self.portal["token_url"],
            data={
                "client_id": self.portal["client_id"],
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        ) as r:
            data = await r.json(content_type=None)

            if r.status >= 400:
                _LOGGER.error(
                    "Kermi refresh failed: HTTP %s response=%s",
                    r.status,
                    _redact(data),
                )
                raise ValueError(
                    f"Token refresh failed: HTTP {r.status}, response={data}"
                )

            return data


def _redact(data):
    if not isinstance(data, dict):
        return data

    redacted = dict(data)
    for key in ("access_token", "refresh_token", "id_token"):
        if key in redacted:
            redacted[key] = "***"
    return redacted
