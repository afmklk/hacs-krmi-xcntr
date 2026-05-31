from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KermiApiClient
from .coordinator import KermiCoordinator


async def async_setup_entry(hass, entry):

    session = async_get_clientsession(hass)

    client = KermiApiClient(
        session,
        entry.data["access_token"],
        entry.data["refresh_token"],
    )

    coordinator = KermiCoordinator(
        hass,
        client,
        entry.data["installation_id"],
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    return True