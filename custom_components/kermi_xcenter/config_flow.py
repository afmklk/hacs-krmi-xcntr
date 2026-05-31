import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN


class KermiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=None):
        if user_input:
            return self.async_create_entry(
                title="Kermi X-Center",
                data=user_input,
            )

        schema = vol.Schema({
            vol.Required("installation_id"): str,
            vol.Required("access_token"): str,
            vol.Required("refresh_token"): str,
            vol.Required("client_id", default="XCenterUI"): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema)