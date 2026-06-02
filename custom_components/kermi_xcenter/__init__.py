from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import KermiApi
from .coordinator import KermiCoordinator
from .token import TokenClient
from .token_store import TokenStore
from .const import DOMAIN, PLATFORMS

async def async_setup_entry(hass, entry):
    session = async_get_clientsession(hass)

    token_client = TokenClient(session)
    token_store = TokenStore(token_client)

    token = entry.data.get("token", {})
    if token:
        await token_store.set_initial(token)

    api = KermiApi(session, token_store)
    coordinator = KermiCoordinator(hass, api, entry.data["installation_id"])
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)