"""Tests for McIntosh coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.mcintosh.coordinator import McIntoshCoordinator, McIntoshData


async def test_coordinator_update_success(
    hass: HomeAssistant,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test successful coordinator update."""
    coordinator = McIntoshCoordinator(hass, mock_mcintosh_client, 'mx160')

    data = await coordinator._async_update_data()

    assert isinstance(data, McIntoshData)
    assert data.power is True
    assert data.volume == 50
    assert data.muted is False
    assert data.source_id == 0
    assert data.source_name == 'HDMI 1'
    assert data.loudness is False


async def test_coordinator_update_power_off(
    hass: HomeAssistant,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test coordinator update when device is off."""
    mock_mcintosh_client.power.get = AsyncMock(return_value=False)

    coordinator = McIntoshCoordinator(hass, mock_mcintosh_client, 'mx160')

    data = await coordinator._async_update_data()

    assert data.power is False
    # volume etc should not be queried when power is off
    mock_mcintosh_client.volume.get.assert_not_called()


async def test_coordinator_update_power_query_fails(
    hass: HomeAssistant,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test coordinator update when power query fails."""
    mock_mcintosh_client.power.get = AsyncMock(return_value=None)

    coordinator = McIntoshCoordinator(hass, mock_mcintosh_client, 'mx160')

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_coordinator_update_connection_error(
    hass: HomeAssistant,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test coordinator update when connection fails."""
    mock_mcintosh_client.power.get = AsyncMock(
        side_effect=ConnectionError('Connection lost')
    )

    coordinator = McIntoshCoordinator(hass, mock_mcintosh_client, 'mx160')

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_coordinator_lipsync_range_fetched_once(
    hass: HomeAssistant,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test lipsync range is fetched only once."""
    coordinator = McIntoshCoordinator(hass, mock_mcintosh_client, 'mx160')

    # first update
    data = await coordinator._async_update_data()
    assert data.lipsync_min == 0
    assert data.lipsync_max == 200

    # second update - range should not be fetched again
    mock_mcintosh_client.lipsync.get_range.reset_mock()
    await coordinator._async_update_data()

    # get_range should not be called again
    mock_mcintosh_client.lipsync.get_range.assert_not_called()
