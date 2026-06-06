import secrets
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .oauth import KermiOAuth
from .token import TokenClient


class KermiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.installation_id = None
        self.verifier = None
        self.state = None
        self.auth_url = None

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self.installation_id = user_input["installation_id"]

            oauth = KermiOAuth()
            self.verifier, challenge = oauth.generate_pkce()
            self.state = secrets.token_urlsafe(24)
            self.auth_url = oauth.build_auth_url(self.state, challenge)

            return await self.async_step_auth()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("installation_id"): str,
                }
            ),
        )

    async def async_step_auth(self, user_input=None):
        errors = {}

        if user_input is not None:
            callback_url = user_input["authorization_response_url"]

            oauth = KermiOAuth()
            code, state = oauth.extract_code_and_state(callback_url)

            if not code:
                errors["authorization_response_url"] = "missing_code"
            elif state != self.state:
                errors["authorization_response_url"] = "invalid_state"
            else:
                session = async_get_clientsession(self.hass)
                token_client = TokenClient(session)

                try:
                    token_data = await token_client.exchange_code(
                        code,
                        self.verifier,
                    )
                except Exception:
                    errors["base"] = "auth_failed"
                else:
                    await self.async_set_unique_id(self.installation_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title="Kermi X-Center",
                        data={
                            "installation_id": self.installation_id,
                            "access_token": token_data["access_token"],
                            "refresh_token": token_data["refresh_token"],
                            "expires_in": token_data.get("expires_in", 3600),
                        },
                    )

        return self.async_show_form(
            step_id="auth",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "open_this_url",
                        default=self.auth_url or "",
                    ): str,
                    vol.Required("authorization_response_url"): str,
                }
            ),
            errors=errors,
        )