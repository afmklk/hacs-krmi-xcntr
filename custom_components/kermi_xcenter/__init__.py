import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN, BASE_URL
from .auth import KermiAuth
from .api import KermiApi
from .coordinator import KermiCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    session = aiohttp_client.async_get_clientsession(hass)

    auth = KermiAuth(session, BASE_URL)

    # stored from config_flow
    auth.set_tokens(entry.data["tokens"])

    api = KermiApi(session, auth, BASE_URL)

    coordinator = KermiCoordinator(
        hass,
        api,
        entry.data["installation_id"],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    return True


async def async_unload_entry(hass, entry):
    hass.data[DOMAIN].pop(entry.entry_id)
    return True