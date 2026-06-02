import voluptuous as vol
from homeassistant import config_entries

DOMAIN = "kermi_xcenter"

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("installation_id"): str,
        vol.Required("access_token"): str,
        vol.Required("refresh_token"): str,
    }
)


class KermiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="Kermi X-Center",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
        )