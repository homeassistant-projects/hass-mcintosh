"""Diagnostics support for McIntosh integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_URL, DOMAIN
from .coordinator import McIntoshCoordinator

# keys to redact from diagnostics output
TO_REDACT = {
    CONF_URL,
    'url',
    'ip',
    'host',
    'serial_port',
    'unique_id',
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: McIntoshCoordinator = hass.data[DOMAIN][entry.entry_id]

    # build diagnostics data
    diagnostics_data: dict[str, Any] = {
        'config_entry': {
            'entry_id': entry.entry_id,
            'version': entry.version,
            'domain': entry.domain,
            'title': entry.title,
            'data': async_redact_data(dict(entry.data), TO_REDACT),
            'options': async_redact_data(dict(entry.options), TO_REDACT),
        },
        'coordinator': {
            'model_id': coordinator.model_id,
            'last_update_success': coordinator.last_update_success,
            'update_interval': str(coordinator.update_interval),
        },
    }

    # add current device state if available
    if coordinator.data:
        diagnostics_data['device_state'] = {
            'power': coordinator.data.power,
            'volume': coordinator.data.volume,
            'muted': coordinator.data.muted,
            'source_id': coordinator.data.source_id,
            'source_name': coordinator.data.source_name,
            'loudness': coordinator.data.loudness,
            'bass_trim': coordinator.data.bass_trim,
            'treble_trim': coordinator.data.treble_trim,
            'lipsync_delay': coordinator.data.lipsync_delay,
            'lipsync_min': coordinator.data.lipsync_min,
            'lipsync_max': coordinator.data.lipsync_max,
            'center_trim': coordinator.data.center_trim,
            'lfe_trim': coordinator.data.lfe_trim,
            'surrounds_trim': coordinator.data.surrounds_trim,
            'height_trim': coordinator.data.height_trim,
        }

    return diagnostics_data
