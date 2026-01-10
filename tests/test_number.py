"""Tests for McIntosh number platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.mcintosh.coordinator import McIntoshCoordinator, McIntoshData
from custom_components.mcintosh.number import (
    McIntoshNumberEntity,
    McIntoshNumberEntityDescription,
    TRIM_NUMBERS,
    _get_device_info,
)


async def test_number_entity_bass_value(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test bass trim number entity value."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=True, bass_trim=30)
    coordinator.client = mock_mcintosh_client

    bass_description = next(d for d in TRIM_NUMBERS if d.key == 'bass_trim')
    device_info = _get_device_info(entry)

    entity = McIntoshNumberEntity(
        coordinator=coordinator,
        description=bass_description,
        model_id='mx160',
        device_info=device_info,
    )
    entity._handle_coordinator_update()

    assert entity._attr_native_value == 30


async def test_number_entity_set_bass(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test setting bass trim value."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=True, bass_trim=0)
    coordinator.client = mock_mcintosh_client
    coordinator.async_request_refresh = AsyncMock()

    bass_description = next(d for d in TRIM_NUMBERS if d.key == 'bass_trim')
    device_info = _get_device_info(entry)

    entity = McIntoshNumberEntity(
        coordinator=coordinator,
        description=bass_description,
        model_id='mx160',
        device_info=device_info,
    )

    await entity.async_set_native_value(50.0)

    mock_mcintosh_client.bass_treble.set_bass.assert_called_once_with(50)
    coordinator.async_request_refresh.assert_called_once()


async def test_number_entity_set_treble(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test setting treble trim value."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=True, treble_trim=0)
    coordinator.client = mock_mcintosh_client
    coordinator.async_request_refresh = AsyncMock()

    treble_description = next(d for d in TRIM_NUMBERS if d.key == 'treble_trim')
    device_info = _get_device_info(entry)

    entity = McIntoshNumberEntity(
        coordinator=coordinator,
        description=treble_description,
        model_id='mx160',
        device_info=device_info,
    )

    await entity.async_set_native_value(-30.0)

    mock_mcintosh_client.bass_treble.set_treble.assert_called_once_with(-30)


async def test_number_entity_lipsync_range_update(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test lipsync range updates from coordinator."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(
        power=True,
        lipsync_delay=50,
        lipsync_min=0,
        lipsync_max=200,
    )
    coordinator.client = mock_mcintosh_client

    lipsync_description = next(d for d in TRIM_NUMBERS if d.key == 'lipsync_delay')
    device_info = _get_device_info(entry)

    entity = McIntoshNumberEntity(
        coordinator=coordinator,
        description=lipsync_description,
        model_id='mx160',
        device_info=device_info,
    )
    entity._handle_coordinator_update()

    assert entity._attr_native_value == 50
    assert entity._attr_native_min_value == 0
    assert entity._attr_native_max_value == 200


async def test_number_entity_channel_trims(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test channel trim entities."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(
        power=True,
        center_trim=10,
        lfe_trim=20,
        surrounds_trim=-10,
        height_trim=5,
    )
    coordinator.client = mock_mcintosh_client
    coordinator.async_request_refresh = AsyncMock()

    device_info = _get_device_info(entry)

    # test center trim
    center_desc = next(d for d in TRIM_NUMBERS if d.key == 'center_trim')
    center_entity = McIntoshNumberEntity(
        coordinator=coordinator,
        description=center_desc,
        model_id='mx160',
        device_info=device_info,
    )
    center_entity._handle_coordinator_update()
    assert center_entity._attr_native_value == 10

    await center_entity.async_set_native_value(15.0)
    mock_mcintosh_client.channel_trim.set_center.assert_called_once_with(15)

    # test LFE trim
    lfe_desc = next(d for d in TRIM_NUMBERS if d.key == 'lfe_trim')
    lfe_entity = McIntoshNumberEntity(
        coordinator=coordinator,
        description=lfe_desc,
        model_id='mx160',
        device_info=device_info,
    )
    lfe_entity._handle_coordinator_update()
    assert lfe_entity._attr_native_value == 20
