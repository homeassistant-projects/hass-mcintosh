"""Tests for McIntosh media player platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.media_player import MediaPlayerState
from homeassistant.core import HomeAssistant

from custom_components.mcintosh.coordinator import McIntoshCoordinator, McIntoshData
from custom_components.mcintosh.media_player import McIntoshMediaPlayer


async def test_media_player_state_on(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test media player state when device is on."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(
        power=True,
        volume=50,
        muted=False,
        source_id=0,
        source_name='HDMI 1',
    )
    coordinator.client = mock_mcintosh_client

    player = McIntoshMediaPlayer(coordinator, entry)

    # simulate coordinator update
    player._handle_coordinator_update()

    assert player._attr_state == MediaPlayerState.ON
    assert player._attr_volume_level == pytest.approx(50 / 99)
    assert player._attr_is_volume_muted is False


async def test_media_player_state_off(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test media player state when device is off."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=False)
    coordinator.client = mock_mcintosh_client

    player = McIntoshMediaPlayer(coordinator, entry)
    player._handle_coordinator_update()

    assert player._attr_state == MediaPlayerState.OFF


async def test_media_player_turn_on(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test turning on the media player."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=False)
    coordinator.client = mock_mcintosh_client
    coordinator.async_request_refresh = AsyncMock()

    player = McIntoshMediaPlayer(coordinator, entry)

    await player.async_turn_on()

    mock_mcintosh_client.power.on.assert_called_once()
    coordinator.async_request_refresh.assert_called_once()


async def test_media_player_turn_off(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test turning off the media player."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=True)
    coordinator.client = mock_mcintosh_client
    coordinator.async_request_refresh = AsyncMock()

    player = McIntoshMediaPlayer(coordinator, entry)

    await player.async_turn_off()

    mock_mcintosh_client.power.off.assert_called_once()
    coordinator.async_request_refresh.assert_called_once()


async def test_media_player_set_volume(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test setting volume."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=True, volume=50)
    coordinator.client = mock_mcintosh_client
    coordinator.async_request_refresh = AsyncMock()

    player = McIntoshMediaPlayer(coordinator, entry)

    await player.async_set_volume_level(0.5)

    mock_mcintosh_client.volume.set.assert_called_once_with(49)


async def test_media_player_mute(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test muting and unmuting."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=True, muted=False)
    coordinator.client = mock_mcintosh_client
    coordinator.async_request_refresh = AsyncMock()

    player = McIntoshMediaPlayer(coordinator, entry)

    await player.async_mute_volume(True)
    mock_mcintosh_client.mute.on.assert_called_once()

    await player.async_mute_volume(False)
    mock_mcintosh_client.mute.off.assert_called_once()


async def test_media_player_select_source(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test selecting source."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=True, source_id=0)
    coordinator.client = mock_mcintosh_client
    coordinator.async_request_refresh = AsyncMock()

    player = McIntoshMediaPlayer(coordinator, entry)

    await player.async_select_source('HDMI 2')

    mock_mcintosh_client.source.set.assert_called_once_with(1)


async def test_media_player_select_invalid_source(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test selecting invalid source is ignored."""
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.options = {}

    coordinator = MagicMock(spec=McIntoshCoordinator)
    coordinator.data = McIntoshData(power=True, source_id=0)
    coordinator.client = mock_mcintosh_client
    coordinator.async_request_refresh = AsyncMock()

    player = McIntoshMediaPlayer(coordinator, entry)

    await player.async_select_source('Invalid Source')

    mock_mcintosh_client.source.set.assert_not_called()
