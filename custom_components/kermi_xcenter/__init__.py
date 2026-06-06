import logging

from homeassistant.exceptions import ConfigEntryAuthFailed
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
                "expires_in": token_data.get(
                    "expires_in",
                    entry.data.get("expires_in", 3600),
                ),
            },
        )

        _LOGGER.debug("Kermi tokens persisted to config entry")

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

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        if _is_auth_error(err):
            raise ConfigEntryAuthFailed(
                "Kermi authentication failed. Re-authentication required."
            ) from err
        raise

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


def _is_auth_error(err):
    text = str(err).lower()

    return (
        "invalid_grant" in text
        or "invalid_token" in text
        or "token refresh failed" in text
        or "token exchange failed" in text
        or "authentication failed" in text
        or "401" in text
    )