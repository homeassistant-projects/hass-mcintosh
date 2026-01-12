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
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
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
    CONF_ENABLE_AUDIO_TRIM,
    CONF_ENABLE_CHANNEL_TRIM,
    CONF_ENABLE_LIPSYNC,
    CONF_ENABLE_LOUDNESS,
    CONF_ENABLED_SOURCE_GROUPS,
    CONF_MAIN_ZONE_NAME,
    CONF_MODEL,
    CONF_POLLING_INTERVAL,
    CONF_SOURCES,
    CONF_URL,
    CONF_ZONE_2_ENABLED,
    CONF_ZONE_2_NAME,
    CONF_ZONE_3_ENABLED,
    CONF_ZONE_3_NAME,
    DEFAULT_MAIN_ZONE_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_URL,
    DEFAULT_ZONE_2_NAME,
    DEFAULT_ZONE_3_NAME,
    DOMAIN,
)
from .pymcintosh import async_get_mcintosh
from .pymcintosh.models import (
    SOURCE_GROUP_ANALOG,
    SOURCE_GROUP_DIGITAL,
    SOURCE_GROUP_HDMI,
    SOURCE_GROUPS,
    SOURCES,
    get_model_config,
)
from .utils import get_connection_overrides

LOG = logging.getLogger(__name__)

# supported baud rates for McIntosh devices
BAUD_RATES = [9600, 19200, 38400, 57600, 115200]


class UnsupportedDeviceError(HomeAssistantError):
    """Error for unsupported device types."""


class McIntoshConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for McIntosh A/V."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._model_id: str | None = None
        self._model_config: dict[str, Any] = {}
        self._connection_data: dict[str, Any] = {}
        self._zone_data: dict[str, Any] = {}
        self._source_groups: list[str] = []
        self._sources_data: dict[str, Any] = {}
        self._features_data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> McIntoshOptionsFlow:
        """Get the options flow for this handler."""
        return McIntoshOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: Select processor model."""
        if user_input is not None:
            self._model_id = user_input[CONF_MODEL]
            self._model_config = get_model_config(self._model_id)
            return await self.async_step_connection()

        # build model options with capability hints
        model_options = []
        for model_id in COMPATIBLE_MODELS:
            config = get_model_config(model_id)
            zones = config.get('zone_count', 2)
            hdmi = config.get('hdmi_count', 8)
            tested = ' - Tested' if config.get('tested') else ''
            label = f"{config['name']} ({hdmi} HDMI, {zones} zones{tested})"
            model_options.append({'value': model_id, 'label': label})

        schema = vol.Schema(
            {
                vol.Required(CONF_MODEL): SelectSelector(
                    SelectSelectorConfig(
                        options=model_options,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id='user',
            data_schema=schema,
        )

    async def async_step_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: Configure connection details."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input.get(CONF_URL, '').strip()

            try:
                loop = asyncio.get_event_loop()
                config_overrides = get_connection_overrides(user_input)

                client = await async_get_mcintosh(
                    self._model_id, url, loop, **config_overrides
                )

                if not await client.device.ping():
                    raise ConnectionError('Device did not respond to ping')

                unique_id = f'{self._model_id}_{url}'
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                self._connection_data = user_input
                return await self.async_step_zones()

            except ConnectionRefusedError:
                errors['base'] = 'connection_refused'
                LOG.warning(f'Connection refused to {url}')
            except TimeoutError:
                errors['base'] = 'connection_timeout'
                LOG.warning(f'Connection timeout to {url}')
            except PermissionError:
                errors['base'] = 'permission_denied'
                LOG.warning(f'Permission denied for {url}')
            except ConnectionError:
                errors['base'] = 'no_response'
                LOG.warning(f'No response from {self._model_id} at {url}')
            except UnsupportedDeviceError:
                errors['base'] = 'unsupported'
                LOG.warning(f'Unsupported device: {self._model_id}')
            except Exception:
                errors['base'] = 'cannot_connect'
                LOG.exception('Unexpected error in config_flow')

        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=DEFAULT_URL): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
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
            step_id='connection',
            data_schema=schema,
            errors=errors,
            description_placeholders={
                'model_name': self._model_config.get('name', self._model_id),
            },
        )

    async def async_step_zones(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 3: Configure zone names."""
        if user_input is not None:
            self._zone_data = user_input
            return await self.async_step_source_groups()

        schema_dict: dict[Any, Any] = {
            vol.Required(
                CONF_MAIN_ZONE_NAME, default=DEFAULT_MAIN_ZONE_NAME
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
        }

        # add zone 2 if supported
        if self._model_config.get('supports_zone_2', True):
            schema_dict[vol.Optional(CONF_ZONE_2_ENABLED, default=True)] = (
                BooleanSelector()
            )
            schema_dict[vol.Optional(CONF_ZONE_2_NAME, default=DEFAULT_ZONE_2_NAME)] = (
                TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))
            )

        # add zone 3 if supported
        if self._model_config.get('supports_zone_3', False):
            schema_dict[vol.Optional(CONF_ZONE_3_ENABLED, default=False)] = (
                BooleanSelector()
            )
            schema_dict[vol.Optional(CONF_ZONE_3_NAME, default=DEFAULT_ZONE_3_NAME)] = (
                TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))
            )

        return self.async_show_form(
            step_id='zones',
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                'model_name': self._model_config.get('name', self._model_id),
                'zone_count': str(self._model_config.get('zone_count', 2)),
            },
        )

    async def async_step_source_groups(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 4: Select source groups to configure."""
        if user_input is not None:
            self._source_groups = user_input.get(CONF_ENABLED_SOURCE_GROUPS, [])

            if SOURCE_GROUP_HDMI in self._source_groups:
                return await self.async_step_sources_hdmi()
            if SOURCE_GROUP_DIGITAL in self._source_groups:
                return await self.async_step_sources_digital()
            if SOURCE_GROUP_ANALOG in self._source_groups:
                return await self.async_step_sources_analog()

            # no sources selected, skip to features
            return await self.async_step_features()

        # build source group options
        group_options = [
            {'value': SOURCE_GROUP_HDMI, 'label': 'HDMI Inputs (1-8)'},
            {'value': SOURCE_GROUP_DIGITAL, 'label': 'Digital Audio (ARC, SPDIF, USB)'},
            {'value': SOURCE_GROUP_ANALOG, 'label': 'Analog Inputs (RCA, Balanced, Phono)'},
        ]

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_ENABLED_SOURCE_GROUPS, default=[SOURCE_GROUP_HDMI]
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=group_options,
                        mode=SelectSelectorMode.LIST,
                        multiple=True,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id='source_groups',
            data_schema=schema,
        )

    async def async_step_sources_hdmi(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 4a: Configure HDMI source names."""
        if user_input is not None:
            self._sources_data.update(user_input)

            if SOURCE_GROUP_DIGITAL in self._source_groups:
                return await self.async_step_sources_digital()
            if SOURCE_GROUP_ANALOG in self._source_groups:
                return await self.async_step_sources_analog()
            return await self.async_step_features()

        schema_dict: dict[Any, Any] = {}
        hdmi_count = self._model_config.get('hdmi_count', 8)

        for source_id in range(hdmi_count):
            default_name = SOURCES.get(source_id, f'HDMI {source_id + 1}')
            schema_dict[vol.Optional(f'source_{source_id}', default='')] = TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            )

        return self.async_show_form(
            step_id='sources_hdmi',
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                'hdmi_count': str(hdmi_count),
            },
        )

    async def async_step_sources_digital(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 4b: Configure digital source names."""
        if user_input is not None:
            self._sources_data.update(user_input)

            if SOURCE_GROUP_ANALOG in self._source_groups:
                return await self.async_step_sources_analog()
            return await self.async_step_features()

        schema_dict: dict[Any, Any] = {}
        digital_sources = SOURCE_GROUPS[SOURCE_GROUP_DIGITAL]

        for source_id in digital_sources:
            schema_dict[vol.Optional(f'source_{source_id}', default='')] = TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            )

        return self.async_show_form(
            step_id='sources_digital',
            data_schema=vol.Schema(schema_dict),
        )

    async def async_step_sources_analog(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 4c: Configure analog source names."""
        if user_input is not None:
            self._sources_data.update(user_input)
            return await self.async_step_features()

        schema_dict: dict[Any, Any] = {}
        analog_sources = SOURCE_GROUPS[SOURCE_GROUP_ANALOG]

        for source_id in analog_sources:
            schema_dict[vol.Optional(f'source_{source_id}', default='')] = TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            )

        return self.async_show_form(
            step_id='sources_analog',
            data_schema=vol.Schema(schema_dict),
        )

    async def async_step_features(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 5: Configure optional features."""
        if user_input is not None:
            self._features_data = user_input
            return await self._create_entry()

        schema_dict: dict[Any, Any] = {}

        if self._model_config.get('supports_loudness', True):
            schema_dict[vol.Optional(CONF_ENABLE_LOUDNESS, default=True)] = (
                BooleanSelector()
            )

        if self._model_config.get('supports_audio_trim', True):
            schema_dict[vol.Optional(CONF_ENABLE_AUDIO_TRIM, default=True)] = (
                BooleanSelector()
            )

        if self._model_config.get('supports_channel_trim', True):
            schema_dict[vol.Optional(CONF_ENABLE_CHANNEL_TRIM, default=False)] = (
                BooleanSelector()
            )

        if self._model_config.get('supports_lipsync', True):
            schema_dict[vol.Optional(CONF_ENABLE_LIPSYNC, default=True)] = (
                BooleanSelector()
            )

        schema_dict[vol.Optional(CONF_POLLING_INTERVAL, default=DEFAULT_SCAN_INTERVAL)] = (
            NumberSelector(
                NumberSelectorConfig(
                    min=10,
                    max=300,
                    step=10,
                    unit_of_measurement='seconds',
                    mode=NumberSelectorMode.SLIDER,
                )
            )
        )

        return self.async_show_form(
            step_id='features',
            data_schema=vol.Schema(schema_dict),
        )

    async def _create_entry(self) -> ConfigFlowResult:
        """Create the config entry with all collected data."""
        # parse sources into dict[int, str]
        sources_config: dict[int, str] = {}
        for key, value in self._sources_data.items():
            if value and value.strip() and key.startswith('source_'):
                source_id = int(key.split('_')[1])
                sources_config[source_id] = value.strip()

        # combine all config data
        config_data = {
            CONF_MODEL: self._model_id,
            **self._connection_data,
            **self._zone_data,
            **self._features_data,
        }

        # store sources in options for easy editing
        options_data = {
            CONF_SOURCES: sources_config,
            CONF_ENABLED_SOURCE_GROUPS: self._source_groups,
        }

        return self.async_create_entry(
            title=f"McIntosh {self._model_config.get('name', self._model_id)}",
            data=config_data,
            options=options_data,
        )


class McIntoshOptionsFlow(OptionsFlow):
    """Handle options flow for McIntosh after initial setup."""

    def __init__(self) -> None:
        """Initialize options flow."""
        self._model_config: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show options menu."""
        model_id = self.config_entry.data.get(CONF_MODEL, 'mx160')
        self._model_config = get_model_config(model_id)

        return self.async_show_menu(
            step_id='init',
            menu_options=['connection', 'zones', 'sources', 'features'],
        )

    async def async_step_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit connection settings."""
        if user_input is not None:
            if CONF_BAUD_RATE in user_input and user_input[CONF_BAUD_RATE]:
                user_input[CONF_BAUD_RATE] = int(user_input[CONF_BAUD_RATE])

            updated = dict(self.config_entry.options)
            updated.update(user_input)
            return self.async_create_entry(title='', data=updated)

        current_url = self.config_entry.options.get(
            CONF_URL, self.config_entry.data.get(CONF_URL, DEFAULT_URL)
        )
        current_baud = self.config_entry.options.get(
            CONF_BAUD_RATE, self.config_entry.data.get(CONF_BAUD_RATE)
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=current_url): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
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
        )

    async def async_step_zones(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit zone configuration."""
        if user_input is not None:
            updated = dict(self.config_entry.options)
            updated.update(user_input)
            return self.async_create_entry(title='', data=updated)

        # get current values
        data = self.config_entry.data
        options = self.config_entry.options

        schema_dict: dict[Any, Any] = {
            vol.Required(
                CONF_MAIN_ZONE_NAME,
                default=options.get(
                    CONF_MAIN_ZONE_NAME,
                    data.get(CONF_MAIN_ZONE_NAME, DEFAULT_MAIN_ZONE_NAME),
                ),
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
        }

        if self._model_config.get('supports_zone_2', True):
            schema_dict[vol.Optional(
                CONF_ZONE_2_ENABLED,
                default=options.get(
                    CONF_ZONE_2_ENABLED, data.get(CONF_ZONE_2_ENABLED, True)
                ),
            )] = BooleanSelector()
            schema_dict[vol.Optional(
                CONF_ZONE_2_NAME,
                default=options.get(
                    CONF_ZONE_2_NAME, data.get(CONF_ZONE_2_NAME, DEFAULT_ZONE_2_NAME)
                ),
            )] = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))

        if self._model_config.get('supports_zone_3', False):
            schema_dict[vol.Optional(
                CONF_ZONE_3_ENABLED,
                default=options.get(
                    CONF_ZONE_3_ENABLED, data.get(CONF_ZONE_3_ENABLED, False)
                ),
            )] = BooleanSelector()
            schema_dict[vol.Optional(
                CONF_ZONE_3_NAME,
                default=options.get(
                    CONF_ZONE_3_NAME, data.get(CONF_ZONE_3_NAME, DEFAULT_ZONE_3_NAME)
                ),
            )] = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))

        return self.async_show_form(
            step_id='zones',
            data_schema=vol.Schema(schema_dict),
        )

    async def async_step_sources(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit source names."""
        if user_input is not None:
            sources_config: dict[int, str] = {}
            for key, value in user_input.items():
                if value and value.strip() and key.startswith('source_'):
                    source_id = int(key.split('_')[1])
                    sources_config[source_id] = value.strip()

            updated = dict(self.config_entry.options)
            updated[CONF_SOURCES] = sources_config
            return self.async_create_entry(title='', data=updated)

        current_sources = self.config_entry.options.get(
            CONF_SOURCES, self.config_entry.data.get(CONF_SOURCES, {})
        )

        # convert string keys to int if needed
        if current_sources and isinstance(next(iter(current_sources.keys())), str):
            current_sources = {int(k): v for k, v in current_sources.items()}

        schema_dict: dict[Any, Any] = {}

        # show all sources organized by group
        for group_name, source_ids in SOURCE_GROUPS.items():
            for source_id in source_ids:
                default_name = SOURCES.get(source_id, '')
                current_name = current_sources.get(source_id, '')
                schema_dict[vol.Optional(f'source_{source_id}', default=current_name)] = (
                    TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))
                )

        return self.async_show_form(
            step_id='sources',
            data_schema=vol.Schema(schema_dict),
        )

    async def async_step_features(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit feature toggles."""
        if user_input is not None:
            updated = dict(self.config_entry.options)
            updated.update(user_input)
            return self.async_create_entry(title='', data=updated)

        data = self.config_entry.data
        options = self.config_entry.options

        schema_dict: dict[Any, Any] = {}

        if self._model_config.get('supports_loudness', True):
            schema_dict[vol.Optional(
                CONF_ENABLE_LOUDNESS,
                default=options.get(
                    CONF_ENABLE_LOUDNESS, data.get(CONF_ENABLE_LOUDNESS, True)
                ),
            )] = BooleanSelector()

        if self._model_config.get('supports_audio_trim', True):
            schema_dict[vol.Optional(
                CONF_ENABLE_AUDIO_TRIM,
                default=options.get(
                    CONF_ENABLE_AUDIO_TRIM, data.get(CONF_ENABLE_AUDIO_TRIM, True)
                ),
            )] = BooleanSelector()

        if self._model_config.get('supports_channel_trim', True):
            schema_dict[vol.Optional(
                CONF_ENABLE_CHANNEL_TRIM,
                default=options.get(
                    CONF_ENABLE_CHANNEL_TRIM, data.get(CONF_ENABLE_CHANNEL_TRIM, False)
                ),
            )] = BooleanSelector()

        if self._model_config.get('supports_lipsync', True):
            schema_dict[vol.Optional(
                CONF_ENABLE_LIPSYNC,
                default=options.get(
                    CONF_ENABLE_LIPSYNC, data.get(CONF_ENABLE_LIPSYNC, True)
                ),
            )] = BooleanSelector()

        schema_dict[vol.Optional(
            CONF_POLLING_INTERVAL,
            default=options.get(
                CONF_POLLING_INTERVAL,
                data.get(CONF_POLLING_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ),
        )] = NumberSelector(
            NumberSelectorConfig(
                min=10,
                max=300,
                step=10,
                unit_of_measurement='seconds',
                mode=NumberSelectorMode.SLIDER,
            )
        )

        return self.async_show_form(
            step_id='features',
            data_schema=vol.Schema(schema_dict),
        )
