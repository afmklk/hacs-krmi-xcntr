import logging
import re

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .api import KermiApi
from .const import DEFAULT_PORTAL, DOMAIN, PLATFORMS, DEFAULT_UPDATE_INTERVAL_MINUTES
from .coordinator import KermiCoordinator
from .token import TokenClient
from .token_store import TokenStore

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry):
    portal = entry.data.get("portal", DEFAULT_PORTAL)
    session = async_get_clientsession(hass)
    token_client = TokenClient(session, portal)

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
        portal,
    )

    coordinator = KermiCoordinator(
        hass,
        api,
        entry.data["installation_id"],
        entry.options.get(
            "update_interval_minutes",
            DEFAULT_UPDATE_INTERVAL_MINUTES,
        ),
        portal,
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

    await er.async_migrate_entries(
        hass,
        entry.entry_id,
        _entity_registry_migration(hass, coordinator),
    )

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


def _entity_registry_migration(hass, coordinator):
    """Return a registry migrator that adds device IDs to legacy unique IDs."""
    legacy_pattern = re.compile(
        r"^(kermi_xcenter(?:_heim_ag)?)_(sensor|switch|number|select)_"
        r"([0-9a-fA-F-]{36})$"
    )
    portal_prefix = (
        "kermi_xcenter"
        if coordinator.portal == DEFAULT_PORTAL
        else f"kermi_xcenter_{coordinator.portal}"
    )
    device_registry = dr.async_get(hass)

    def migrate(entry):
        match = legacy_pattern.fullmatch(entry.unique_id)
        if match is None:
            return None

        old_prefix, platform, config_id = match.groups()
        expected_old_prefix = portal_prefix
        if old_prefix != expected_old_prefix:
            return None

        device_id = None
        if entry.device_id and (device := device_registry.async_get(entry.device_id)):
            for identifier_domain, identifier in device.identifiers:
                if identifier_domain == portal_prefix:
                    device_id = identifier
                    break

        candidates = [
            datapoint
            for datapoint in coordinator.data.get("datapoints", {}).values()
            if datapoint.get("config_id") == config_id
        ]
        if device_id is None:
            if len(candidates) != 1:
                return None
            device_id = candidates[0].get("device_id") or "system"

        new_unique_id = (
            f"{portal_prefix}_{platform}_{device_id}_{config_id}"
        )
        if new_unique_id == entry.unique_id:
            return None

        return {"new_unique_id": new_unique_id}

    return migrate


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
