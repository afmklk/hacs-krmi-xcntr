import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN


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
            await self.async_set_unique_id(user_input["installation_id"])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Kermi X-Center",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
        )

    async def async_step_reconfigure(self, user_input=None):
        entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        if user_input is not None:
            return self.async_update_reload_and_abort(
                entry,
                data_updates=user_input,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "installation_id",
                        default=entry.data.get("installation_id", ""),
                    ): str,
                    vol.Required(
                        "access_token",
                        default=entry.data.get("access_token", ""),
                    ): str,
                    vol.Required(
                        "refresh_token",
                        default=entry.data.get("refresh_token", ""),
                    ): str,
                }
            ),
        )