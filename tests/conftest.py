"""Common fixtures for McIntosh tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from custom_components.mcintosh.const import (
    CONF_BAUD_RATE,
    CONF_MODEL,
    CONF_URL,
    DOMAIN,
)


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Mock setting up a config entry."""
    with patch(
        'custom_components.mcintosh.async_setup_entry',
        return_value=True,
    ) as mock_setup:
        yield mock_setup


@pytest.fixture
def mock_config_entry_data() -> dict:
    """Return mock config entry data."""
    return {
        CONF_MODEL: 'mx160',
        CONF_URL: 'socket://192.168.1.100:84',
    }


@pytest.fixture
def mock_mcintosh_client() -> MagicMock:
    """Return a mock McIntosh client."""
    client = MagicMock()

    # power control
    client.power = AsyncMock()
    client.power.get = AsyncMock(return_value=True)
    client.power.on = AsyncMock()
    client.power.off = AsyncMock()

    # volume control
    client.volume = AsyncMock()
    client.volume.get = AsyncMock(return_value=50)
    client.volume.set = AsyncMock()
    client.volume.up = AsyncMock()
    client.volume.down = AsyncMock()

    # mute control
    client.mute = AsyncMock()
    client.mute.get = AsyncMock(return_value=False)
    client.mute.on = AsyncMock()
    client.mute.off = AsyncMock()

    # source control
    client.source = AsyncMock()
    client.source.get = AsyncMock(return_value={'source': 0, 'name': 'HDMI 1'})
    client.source.set = AsyncMock()

    # loudness control
    client.loudness = AsyncMock()
    client.loudness.get = AsyncMock(return_value=False)
    client.loudness.on = AsyncMock()
    client.loudness.off = AsyncMock()

    # bass/treble control
    client.bass_treble = AsyncMock()
    client.bass_treble.get_bass = AsyncMock(return_value=0)
    client.bass_treble.get_treble = AsyncMock(return_value=0)
    client.bass_treble.set_bass = AsyncMock()
    client.bass_treble.set_treble = AsyncMock()

    # lipsync control
    client.lipsync = AsyncMock()
    client.lipsync.get = AsyncMock(return_value=0)
    client.lipsync.set = AsyncMock()
    client.lipsync.get_range = AsyncMock(return_value={'min': 0, 'max': 200})

    # channel trim control
    client.channel_trim = AsyncMock()
    client.channel_trim.get_center = AsyncMock(return_value=0)
    client.channel_trim.get_lfe = AsyncMock(return_value=0)
    client.channel_trim.get_surrounds = AsyncMock(return_value=0)
    client.channel_trim.get_height = AsyncMock(return_value=0)
    client.channel_trim.set_center = AsyncMock()
    client.channel_trim.set_lfe = AsyncMock()
    client.channel_trim.set_surrounds = AsyncMock()
    client.channel_trim.set_height = AsyncMock()

    # device control
    client.device = AsyncMock()
    client.device.ping = AsyncMock(return_value=True)
    client.device.name = AsyncMock(return_value='MX160')

    return client
