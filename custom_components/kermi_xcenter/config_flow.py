import voluptuous as vol
from homeassistant import config_entries

from .oauth import KermiOAuth


class KermiConfigFlow(config_entries.ConfigFlow, domain="kermi_xcenter"):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        oauth = KermiOAuth()

        verifier, challenge = oauth.generate_pkce()

        self.context["verifier"] = verifier
        self.context["state"] = "kermi_state"

        redirect_uri = self.hass.config.api.base_url + "/auth/external/callback"

        url = oauth.build_auth_url(
            redirect_uri=redirect_uri,
            state="kermi_state",
            challenge=challenge,
        )

        self.context["redirect_uri"] = redirect_uri

        return self.async_external_step(step_id="auth", url=url)

    async def async_step_auth(self, user_input):
        return self.async_create_entry(
            title="Kermi X-Center",
            data=user_input,
        )