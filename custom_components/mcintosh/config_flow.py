"""Config flow for easy setup"""

from __future__ import annotations

import logging
import asyncio
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_URL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector

from pymcintosh import async_get_mcintosh
from pymcintosh.models import SUPPORTED_MODELS, get_model_config

from .utils import get_connection_overrides
from .const import CONF_BAUD_RATE, CONF_MODEL, DEFAULT_URL, DOMAIN, COMPATIBLE_MODELS

LOG = logging.getLogger(__name__)

ERROR_CANNOT_CONNECT = {'base': 'cannot_connect'}
ERROR_UNSUPPORTED = {'base': 'unsupported'}

# supported baud rates for McIntosh devices
BAUD_RATES = [9600, 19200, 38400, 57600, 115200]


class UnsupportedDeviceError(HomeAssistantError):
    """Error for unsupported device types."""


class McIntoshConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        """Initialize the McIntosh config flow."""
        pass

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return McIntoshOptionsFlow(config_entry)

    @staticmethod
    def step_user_schema(supported_models) -> vol.Schema:
        schema = vol.Schema(
            {
                vol.Required(CONF_MODEL): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=supported_models,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_URL, default=DEFAULT_URL
                ): cv.string,  # this should NOT be cv.url (since also can be a path)
                vol.Optional(CONF_BAUD_RATE): vol.In(BAUD_RATES),
            }
        )
        return schema

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None, errors=None
    ) -> FlowResult:
        """Handle the initial step of selecting model to configure."""
        errors: dict[str, str] = {}

        if user_input is not None:
            LOG.info(f'Config flow user input: {user_input}')

            model_id = user_input[CONF_MODEL]
            url = user_input.get(CONF_URL).strip()

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

            except ConnectionError as e:
                errors = ERROR_CANNOT_CONNECT
                LOG.warning(f'Failed config_flow: {errors}', exc_info=e)
            except UnsupportedDeviceError as e:
                errors = ERROR_UNSUPPORTED
                LOG.warning(f'Failed config_flow: {errors}', exc_info=e)
            except Exception as e:
                errors = ERROR_CANNOT_CONNECT
                LOG.exception(f'Unexpected error in config_flow: {e}')
            else:
                return self.async_create_entry(title='McIntosh', data=user_input)

        # no user input yet, display the initial configuration form
        LOG.debug(f'Starting McIntosh config flow with models: {COMPATIBLE_MODELS}')

        schema = McIntoshConfigFlow.step_user_schema(COMPATIBLE_MODELS)
        return self.async_show_form(step_id='user', data_schema=schema, errors=errors)


class McIntoshOptionsFlow(OptionsFlow):
    """Handles options flow for the component after it has already been setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Manage the options for the custom component."""
        return self.async_show_menu(
            step_id='init',
            menu_options=['connection', 'sources']
        )

    async def async_step_connection(
        self, user_input: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Configure connection settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not errors:
                return self.async_create_entry(title='', data=user_input)

        current_url = self._config_entry.options.get(
            CONF_URL, self._config_entry.data.get(CONF_URL, DEFAULT_URL)
        )
        current_baud = self._config_entry.options.get(
            CONF_BAUD_RATE, self._config_entry.data.get(CONF_BAUD_RATE)
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=current_url): cv.string,
                vol.Optional(CONF_BAUD_RATE, default=current_baud): vol.In(BAUD_RATES),
            }
        )
        return self.async_show_form(step_id='connection', data_schema=schema, errors=errors)

    async def async_step_sources(
        self, user_input: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Configure custom source names."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # filter out empty source names and convert to dict
            sources_config = {}
            for key, value in user_input.items():
                if value and value.strip():
                    # extract source number from key (e.g., 'source_0' -> 0)
                    source_id = int(key.split('_')[1])
                    sources_config[source_id] = value.strip()

            if not errors:
                # merge with existing options, preserving other settings
                updated_options = dict(self._config_entry.options)
                updated_options[CONF_SOURCES] = sources_config
                return self.async_create_entry(title='', data=updated_options)

        # get current source configuration
        current_sources = self._config_entry.options.get(
            CONF_SOURCES, self._config_entry.data.get(CONF_SOURCES, {})
        )

        # import SOURCES from pymcintosh for default names
        from pymcintosh.models import SOURCES

        # build schema with commonly used sources (HDMI 1-8, first few digital/analog)
        # users can customize the ones they use
        common_sources = list(range(8)) + [17, 18, 24]  # HDMI 1-8, USB Audio, Analog 1, Phono
        schema_dict = {}

        for source_id in common_sources:
            default_name = current_sources.get(source_id, SOURCES.get(source_id, ''))
            schema_dict[vol.Optional(f'source_{source_id}', default=default_name)] = cv.string

        schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id='sources',
            data_schema=schema,
            errors=errors,
            description_placeholders={
                'info': 'Configure custom names for your sources. Leave blank to use defaults.'
            }
        )
