import secrets
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import OptionsFlowWithReload
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL_MINUTES
from .oauth import KermiOAuth
from .token import TokenClient

class KermiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.installation_id = None
        self.verifier = None
        self.state = None
        self.auth_url = None
        self.reauth_entry = None

    @staticmethod
    def async_get_options_flow(config_entry):
        return KermiOptionsFlow()

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self.installation_id = user_input["installation_id"]

            await self.async_set_unique_id(self.installation_id)
            self._abort_if_unique_id_configured()

            return await self._start_oauth_flow()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("installation_id"): str,
                }
            ),
        )

    async def async_step_reauth(self, entry_data):
        self.reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        self.installation_id = entry_data["installation_id"]

        return await self._start_oauth_flow()

    async def _start_oauth_flow(self):
        oauth = KermiOAuth()
        self.verifier, challenge = oauth.generate_pkce()
        self.state = secrets.token_urlsafe(24)
        self.auth_url = oauth.build_auth_url(self.state, challenge)

        return await self.async_step_auth()

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
                    data = {
                        "installation_id": self.installation_id,
                        "access_token": token_data["access_token"],
                        "refresh_token": token_data["refresh_token"],
                        "expires_in": token_data.get("expires_in", 3600),
                    }

                    if self.reauth_entry is not None:
                        self.hass.config_entries.async_update_entry(
                            self.reauth_entry,
                            data={
                                **self.reauth_entry.data,
                                **data,
                            },
                        )

                        await self.hass.config_entries.async_reload(
                            self.reauth_entry.entry_id
                        )

                        return self.async_abort(
                            reason="reauth_successful"
                        )

                    return self.async_create_entry(
                        title="Kermi X-Center",
                        data=data,
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

class KermiOptionsFlow(OptionsFlowWithReload):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    "update_interval_minutes": int(
                        user_input["update_interval_minutes"]
                    ),
                },
            )

        current = self.config_entry.options.get(
            "update_interval_minutes",
            DEFAULT_UPDATE_INTERVAL_MINUTES,
        )

        return self.async_show_form(
            step_id="init",
            description_placeholders={
                "default_interval": str(DEFAULT_UPDATE_INTERVAL_MINUTES),
				"description": (
					"Configure how often Home Assistant refreshes "
					"data from the Kermi cloud."
				)
            },
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "update_interval_minutes",
                        default=str(current),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {
                                    "value": "1",
                                    "label": "1 minute",
                                },
                                {
                                    "value": "2",
                                    "label": "2 minutes",
                                },
                                {
                                    "value": "5",
                                    "label": "5 minutes",
                                },
                                {
                                    "value": "10",
                                    "label": "10 minutes",
                                },
                                {
                                    "value": "15",
                                    "label": "15 minutes",
                                },
                                {
                                    "value": "30",
                                    "label": "30 minutes",
                                },
                                {
                                    "value": "60",
                                    "label": "60 minutes",
                                },
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )