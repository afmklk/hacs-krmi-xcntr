import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN


class KermiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="Kermi X-Center",
                data={
                    "installation_id": user_input["installation_id"],
                    "tokens": {
                        "access_token": user_input["access_token"],
                        "refresh_token": user_input.get("refresh_token"),
                        "expires_in": 3600,
                    },
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("installation_id"): str,
                vol.Required("access_token"): str,
                vol.Optional("refresh_token"): str,
            }),
        )