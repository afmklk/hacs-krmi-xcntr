from .api import KermiApiClient
from .coordinator import KermiCoordinator


async def async_setup_entry(hass, entry):
    session = hass.helpers.aiohttp_client.async_get_clientsession()

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
    hass.data.setdefault("kermi_xcenter", {})[entry.entry_id] = coordinator

    return True