import logging

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KermiApi
from .const import DOMAIN, PLATFORMS
from .coordinator import KermiCoordinator
from .token import TokenClient
from .token_store import TokenStore

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry):
    session = async_get_clientsession(hass)
    token_client = TokenClient(session)

    def update_tokens(token_data):
        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get(
                    "refresh_token",
                    entry.data.get("refresh_token"),
                ),
            },
        )

    token_store = TokenStore(
        token_client,
        update_callback=update_tokens,
    )

    await token_store.set_initial(
        {
            "access_token": entry.data["access_token"],
            "refresh_token": entry.data["refresh_token"],
            "expires_in": entry.data.get("expires_in", 3600),
        }
    )

    api = KermiApi(
        session,
        token_store,
        entry.data["installation_id"],
    )

    coordinator = KermiCoordinator(
        hass,
        api,
        entry.data["installation_id"],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(hass, entry):
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok