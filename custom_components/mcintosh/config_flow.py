"""Config flow for McIntosh A/V integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    COMPATIBLE_MODELS,
    CONF_BAUD_RATE,
    CONF_MODEL,
    CONF_SOURCES,
    CONF_URL,
    DEFAULT_URL,
    DOMAIN,
)
from .pymcintosh import async_get_mcintosh
from .pymcintosh.models import SOURCES
from .utils import get_connection_overrides

LOG = logging.getLogger(__name__)

# supported baud rates for McIntosh devices
BAUD_RATES = [9600, 19200, 38400, 57600, 115200]


class UnsupportedDeviceError(HomeAssistantError):
    """Error for unsupported device types."""


class McIntoshConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for McIntosh A/V."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> McIntoshOptionsFlow:
        """Get the options flow for this handler."""
        return McIntoshOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step of selecting model to configure."""
        errors: dict[str, str] = {}

        if user_input is not None:
            LOG.info(f'Config flow user input: {user_input}')

            model_id = user_input[CONF_MODEL]
            url = user_input.get(CONF_URL, '').strip()

            try:
                loop = asyncio.get_event_loop()
                config_overrides = get_connection_overrides(user_input)

                # connect to the device to confirm everything works
                client = await async_get_mcintosh(
                    model_id, url, loop, **config_overrides
                )

                # test connection with ping
                if not await client.device.ping():
                    raise ConnectionError('Device did not respond to ping')

                # unique_id is url + model (McIntosh doesn't expose serial via RS232)
                unique_id = f'{model_id}_{url}'

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

            except ConnectionError:
                errors['base'] = 'cannot_connect'
                LOG.warning(f'Failed to connect to {model_id} at {url}')
            except UnsupportedDeviceError:
                errors['base'] = 'unsupported'
                LOG.warning(f'Unsupported device: {model_id}')
            except Exception:
                errors['base'] = 'cannot_connect'
                LOG.exception('Unexpected error in config_flow')
            else:
                return self.async_create_entry(
                    title=f'McIntosh {model_id.upper()}',
                    data=user_input,
                )

        # build schema with modern selectors
        schema = vol.Schema(
            {
                vol.Required(CONF_MODEL): SelectSelector(
                    SelectSelectorConfig(
                        options=COMPATIBLE_MODELS,
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key='model_id',
                    )
                ),
                vol.Required(CONF_URL, default=DEFAULT_URL): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.TEXT,
                    )
                ),
                vol.Optional(CONF_BAUD_RATE): SelectSelector(
                    SelectSelectorConfig(
                        options=[str(rate) for rate in BAUD_RATES],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id='user',
            data_schema=schema,
            errors=errors,
        )


class McIntoshOptionsFlow(OptionsFlow):
    """Handle options flow for the component after it has already been setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for the custom component."""
        return self.async_show_menu(
            step_id='init',
            menu_options=['connection', 'sources'],
        )

    async def async_step_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure connection settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # convert baud rate string back to int if present
            if CONF_BAUD_RATE in user_input and user_input[CONF_BAUD_RATE]:
                user_input[CONF_BAUD_RATE] = int(user_input[CONF_BAUD_RATE])
            return self.async_create_entry(title='', data=user_input)

        current_url = self.config_entry.options.get(
            CONF_URL, self.config_entry.data.get(CONF_URL, DEFAULT_URL)
        )
        current_baud = self.config_entry.options.get(
            CONF_BAUD_RATE, self.config_entry.data.get(CONF_BAUD_RATE)
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=current_url): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.TEXT,
                    )
                ),
                vol.Optional(
                    CONF_BAUD_RATE,
                    default=str(current_baud) if current_baud else None,
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[str(rate) for rate in BAUD_RATES],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id='connection',
            data_schema=schema,
            errors=errors,
        )

    async def async_step_sources(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure custom source names."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # filter out empty source names and convert to dict
            sources_config: dict[int, str] = {}
            for key, value in user_input.items():
                if value and value.strip():
                    # extract source number from key (e.g., 'source_0' -> 0)
                    source_id = int(key.split('_')[1])
                    sources_config[source_id] = value.strip()

            # merge with existing options, preserving other settings
            updated_options = dict(self.config_entry.options)
            updated_options[CONF_SOURCES] = sources_config
            return self.async_create_entry(title='', data=updated_options)

        # get current source configuration
        current_sources = self.config_entry.options.get(
            CONF_SOURCES, self.config_entry.data.get(CONF_SOURCES, {})
        )

        # build schema with commonly used sources (HDMI 1-8, first few digital/analog)
        common_sources = list(range(8)) + [17, 18, 24]  # HDMI 1-8, USB Audio, Analog 1, Phono
        schema_dict: dict[vol.Optional, TextSelector] = {}

        for source_id in common_sources:
            default_name = current_sources.get(source_id, SOURCES.get(source_id, ''))
            schema_dict[vol.Optional(f'source_{source_id}', default=default_name)] = (
                TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.TEXT,
                    )
                )
            )

        schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id='sources',
            data_schema=schema,
            errors=errors,
        )
