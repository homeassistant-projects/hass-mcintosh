"""Tests for McIntosh switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.mcintosh.coordinator import McIntoshCoordinator, McIntoshData
from custom_components.mcintosh.switch import McIntoshLoudnessSwitch


async def test_switch_state_on(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test switch state when loudness is on."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=True, loudness=True)
    coordinator.client = mock_mcintosh_client

    switch = McIntoshLoudnessSwitch(coordinator, entry)
    switch._handle_coordinator_update()

    assert switch._attr_is_on is True


async def test_switch_state_off(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test switch state when loudness is off."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=True, loudness=False)
    coordinator.client = mock_mcintosh_client

    switch = McIntoshLoudnessSwitch(coordinator, entry)
    switch._handle_coordinator_update()

    assert switch._attr_is_on is False


async def test_switch_turn_on(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test turning on loudness."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=True, loudness=False)
    coordinator.client = mock_mcintosh_client
    coordinator.async_request_refresh = AsyncMock()

    switch = McIntoshLoudnessSwitch(coordinator, entry)

    await switch.async_turn_on()

    mock_mcintosh_client.loudness.on.assert_called_once()
    coordinator.async_request_refresh.assert_called_once()


async def test_switch_turn_off(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test turning off loudness."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=True, loudness=True)
    coordinator.client = mock_mcintosh_client
    coordinator.async_request_refresh = AsyncMock()

    switch = McIntoshLoudnessSwitch(coordinator, entry)

    await switch.async_turn_off()

    mock_mcintosh_client.loudness.off.assert_called_once()
    coordinator.async_request_refresh.assert_called_once()
