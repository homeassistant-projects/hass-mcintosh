"""Tests for McIntosh config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.mcintosh.const import (
    CONF_BAUD_RATE,
    CONF_MODEL,
    CONF_URL,
    DOMAIN,
)


async def test_form_user(hass: HomeAssistant, mock_mcintosh_client: MagicMock) -> None:
    """Test we get the user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )
    assert result['type'] is FlowResultType.FORM
    assert result['step_id'] == 'user'
    assert result['errors'] == {}


async def test_form_user_success(
    hass: HomeAssistant,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test successful user form submission."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )

    with patch(
        'custom_components.mcintosh.config_flow.async_get_mcintosh',
        return_value=mock_mcintosh_client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            {
                CONF_MODEL: 'mx160',
                CONF_URL: 'socket://192.168.1.100:84',
            },
        )
        await hass.async_block_till_done()

    assert result['type'] is FlowResultType.CREATE_ENTRY
    assert result['title'] == 'McIntosh MX160'
    assert result['data'] == {
        CONF_MODEL: 'mx160',
        CONF_URL: 'socket://192.168.1.100:84',
    }


async def test_form_user_cannot_connect(
    hass: HomeAssistant,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )

    mock_mcintosh_client.device.ping = AsyncMock(return_value=False)

    with patch(
        'custom_components.mcintosh.config_flow.async_get_mcintosh',
        return_value=mock_mcintosh_client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            {
                CONF_MODEL: 'mx160',
                CONF_URL: 'socket://192.168.1.100:84',
            },
        )

    assert result['type'] is FlowResultType.FORM
    assert result['errors'] == {'base': 'cannot_connect'}


async def test_form_user_connection_error(
    hass: HomeAssistant,
) -> None:
    """Test we handle connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )

    with patch(
        'custom_components.mcintosh.config_flow.async_get_mcintosh',
        side_effect=ConnectionError('Connection failed'),
    ):
        result = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            {
                CONF_MODEL: 'mx160',
                CONF_URL: 'socket://192.168.1.100:84',
            },
        )

    assert result['type'] is FlowResultType.FORM
    assert result['errors'] == {'base': 'cannot_connect'}


async def test_form_user_already_configured(
    hass: HomeAssistant,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test we handle already configured."""
    # create an existing entry
    entry = config_entries.ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title='McIntosh MX160',
        data={
            CONF_MODEL: 'mx160',
            CONF_URL: 'socket://192.168.1.100:84',
        },
        source=config_entries.SOURCE_USER,
        unique_id='mx160_socket://192.168.1.100:84',
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )

    with patch(
        'custom_components.mcintosh.config_flow.async_get_mcintosh',
        return_value=mock_mcintosh_client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            {
                CONF_MODEL: 'mx160',
                CONF_URL: 'socket://192.168.1.100:84',
            },
        )

    assert result['type'] is FlowResultType.ABORT
    assert result['reason'] == 'already_configured'


async def test_form_with_baud_rate(
    hass: HomeAssistant,
    mock_mcintosh_client: MagicMock,
) -> None:
    """Test form submission with custom baud rate."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )

    with patch(
        'custom_components.mcintosh.config_flow.async_get_mcintosh',
        return_value=mock_mcintosh_client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            {
                CONF_MODEL: 'mx160',
                CONF_URL: '/dev/ttyUSB0',
                CONF_BAUD_RATE: '9600',
            },
        )
        await hass.async_block_till_done()

    assert result['type'] is FlowResultType.CREATE_ENTRY
    assert result['data'][CONF_BAUD_RATE] == '9600'
