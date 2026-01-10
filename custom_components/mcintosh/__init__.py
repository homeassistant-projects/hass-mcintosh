"""The McIntosh A/V integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_MODEL, CONF_URL, DOMAIN
from .coordinator import McIntoshCoordinator
from .pymcintosh import async_get_mcintosh
from .utils import get_connection_overrides

LOG = logging.getLogger(__name__)

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.SWITCH, Platform.NUMBER]

type McIntoshConfigEntry = ConfigEntry[McIntoshCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: McIntoshConfigEntry) -> bool:
    """Set up McIntosh from a config entry."""
    config = entry.data
    url = config[CONF_URL]
    model_id = config[CONF_MODEL]

    try:
        client = await async_get_mcintosh(
            model_id, url, hass.loop, **get_connection_overrides(config)
        )
    except Exception as err:
        raise ConfigEntryNotReady(f'Connection failed to {model_id} @ {url}') from err

    coordinator = McIntoshCoordinator(hass, client, model_id)
    coordinator.config_entry = entry

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    LOG.info(f'Reloading after configuration change: {entry.title}')
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
