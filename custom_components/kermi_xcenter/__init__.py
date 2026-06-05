from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import KermiApi
from .coordinator import KermiCoordinator
from .token import TokenClient
from .token_store import TokenStore
from .const import DOMAIN, PLATFORMS

import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    session = async_get_clientsession(hass)
    token_client = TokenClient(session)
    token_store = TokenStore(token_client)
    
    _LOGGER.warning(
    "Config entry loaded. installation=%s access=%s refresh=%s",
    entry.data.get("installation_id"),
    bool(entry.data.get("access_token")),
    bool(entry.data.get("refresh_token")),
    )
    
    await token_store.set_initial(
        {
            "access_token": entry.data["access_token"],
            "refresh_token": entry.data["refresh_token"],
            "expires_in": 3600,
        }
    )

    _LOGGER.warning(
        "Access token starts with: %s",
        entry.data["access_token"][:50],
    )

    _LOGGER.warning(
        "TokenStore initialized. access=%s refresh=%s",
        bool(token_store.access_token),
        bool(token_store.refresh_token),
    )

    api = KermiApi(
        session,
        token_store,
        entry.data["installation_id"],
    )
    coordinator = KermiCoordinator(hass, api, entry.data["installation_id"])
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)