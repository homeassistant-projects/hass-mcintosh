"""Tests for McIntosh diagnostics."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.mcintosh.const import CONF_MODEL, CONF_URL, DOMAIN
from custom_components.mcintosh.coordinator import McIntoshCoordinator, McIntoshData
from custom_components.mcintosh.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test diagnostics output."""
    # create mock coordinator with data
    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.model_id = 'mx160'
    coordinator.last_update_success = True
    coordinator.update_interval = '0:00:30'
    coordinator.data = McIntoshData(
        power=True,
        volume=50,
        muted=False,
        source_id=0,
        source_name='HDMI 1',
        loudness=False,
        bass_trim=0,
        treble_trim=0,
        lipsync_delay=10,
        lipsync_min=0,
        lipsync_max=200,
        center_trim=0,
        lfe_trim=0,
        surrounds_trim=0,
        height_trim=0,
    )

    # create mock config entry
    entry = MagicMock()
    entry.entry_id = 'test_entry_id'
    entry.version = 1
    entry.domain = DOMAIN
    entry.title = 'McIntosh MX160'
    entry.data = mock_config_entry_data
    entry.options = {}

    # setup hass data
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    # get diagnostics
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    # verify structure
    assert 'config_entry' in diagnostics
    assert 'coordinator' in diagnostics
    assert 'device_state' in diagnostics

    # verify sensitive data is redacted
    assert diagnostics['config_entry']['data'][CONF_URL] == '**REDACTED**'

    # verify device state
    assert diagnostics['device_state']['power'] is True
    assert diagnostics['device_state']['volume'] == 50
    assert diagnostics['device_state']['source_id'] == 0


async def test_diagnostics_no_data(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
) -> None:
    """Test diagnostics when coordinator has no data."""
    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.model_id = 'mx160'
    coordinator.last_update_success = False
    coordinator.update_interval = '0:00:30'
    coordinator.data = None

    entry = MagicMock()
    entry.entry_id = 'test_entry_id'
    entry.version = 1
    entry.domain = DOMAIN
    entry.title = 'McIntosh MX160'
    entry.data = mock_config_entry_data
    entry.options = {}

    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert 'device_state' not in diagnostics
    assert diagnostics['coordinator']['last_update_success'] is False
