"""Home Assistant McIntosh Number Platform"""

import logging
from typing import Optional

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DeviceClientDetails
from .const import CONF_MODEL, DOMAIN
from .pymcintosh.models import get_model_config

LOG = logging.getLogger(__name__)


def _get_device_info(config_entry: ConfigEntry) -> DeviceInfo:
    """Get device info for grouping entities."""
    model_id = config_entry.data[CONF_MODEL]
    model_config = get_model_config(model_id)
    manufacturer = 'McIntosh'
    model_name = model_config['name']
    device_unique_id = f'{DOMAIN}_{model_id}'.lower().replace(' ', '_')

    return DeviceInfo(
        identifiers={(DOMAIN, device_unique_id)},
        manufacturer=manufacturer,
        model=model_name,
        name=f'{manufacturer} {model_name}',
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    if data := hass.data[DOMAIN][config_entry.entry_id]:
        entities = [
            McIntoshBassNumber(config_entry, data),
            McIntoshTrebleNumber(config_entry, data),
            McIntoshLipsyncNumber(config_entry, data),
            McIntoshCenterTrimNumber(config_entry, data),
            McIntoshLFETrimNumber(config_entry, data),
            McIntoshSurroundsTrimNumber(config_entry, data),
            McIntoshHeightTrimNumber(config_entry, data),
        ]
        async_add_entities(new_entities=entities, update_before_add=True)
    else:
        LOG.error(
            f'missing pre-connected client for {config_entry}, cannot create number entities'
        )


class McIntoshBassNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_native_min_value = -120
    _attr_native_max_value = 120
    _attr_native_step = 10
    _attr_mode = NumberMode.SLIDER
    _attr_icon = 'mdi:music-clef-bass'

    def __init__(self, config_entry: ConfigEntry, details: DeviceClientDetails) -> None:
        self._config_entry = config_entry
        self._details = details
        self._client = details.client

        model_id = config_entry.data[CONF_MODEL]
        self._attr_unique_id = f'{DOMAIN}_{model_id}_bass'.lower().replace(' ', '_')
        self._attr_name = 'Bass Trim'
        self._attr_native_unit_of_measurement = 'x0.1dB'
        self._attr_device_info = _get_device_info(config_entry)

    async def async_added_to_hass(self) -> None:
        await self.async_update()

    async def async_update(self):
        """Retrieve the latest state."""
        LOG.debug(f'updating {self.unique_id}')

        try:
            value = await self._client.bass_treble.get_bass()
            if value is not None:
                self._attr_native_value = value
        except Exception as e:
            LOG.exception(f'could not update {self.unique_id}: {e}')

    async def async_set_native_value(self, value: float) -> None:
        """Set bass trim level."""
        await self._client.bass_treble.set_bass(int(value))
        self.async_schedule_update_ha_state(force_refresh=True)


class McIntoshTrebleNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_native_min_value = -120
    _attr_native_max_value = 120
    _attr_native_step = 10
    _attr_mode = NumberMode.SLIDER
    _attr_icon = 'mdi:music-clef-treble'

    def __init__(self, config_entry: ConfigEntry, details: DeviceClientDetails) -> None:
        self._config_entry = config_entry
        self._details = details
        self._client = details.client

        model_id = config_entry.data[CONF_MODEL]
        self._attr_unique_id = f'{DOMAIN}_{model_id}_treble'.lower().replace(' ', '_')
        self._attr_name = 'Treble Trim'
        self._attr_native_unit_of_measurement = 'x0.1dB'
        self._attr_device_info = _get_device_info(config_entry)

    async def async_added_to_hass(self) -> None:
        await self.async_update()

    async def async_update(self):
        """Retrieve the latest state."""
        LOG.debug(f'updating {self.unique_id}')

        try:
            value = await self._client.bass_treble.get_treble()
            if value is not None:
                self._attr_native_value = value
        except Exception as e:
            LOG.exception(f'could not update {self.unique_id}: {e}')

    async def async_set_native_value(self, value: float) -> None:
        """Set treble trim level."""
        await self._client.bass_treble.set_treble(int(value))
        self.async_schedule_update_ha_state(force_refresh=True)


class McIntoshLipsyncNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX
    _attr_icon = 'mdi:timer-outline'

    def __init__(self, config_entry: ConfigEntry, details: DeviceClientDetails) -> None:
        self._config_entry = config_entry
        self._details = details
        self._client = details.client

        model_id = config_entry.data[CONF_MODEL]
        self._attr_unique_id = f'{DOMAIN}_{model_id}_lipsync'.lower().replace(' ', '_')
        self._attr_name = 'Lipsync Delay'
        self._attr_native_unit_of_measurement = 'ms'
        self._attr_device_info = _get_device_info(config_entry)

        # will be set dynamically from device
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1

    async def async_added_to_hass(self) -> None:
        # query device for actual lipsync range
        try:
            range_info = await self._client.lipsync.get_range()
            if range_info:
                self._attr_native_min_value = range_info['min']
                self._attr_native_max_value = range_info['max']
                LOG.debug(f'lipsync range: {range_info}')
        except Exception as e:
            LOG.warning(f'could not get lipsync range, using defaults: {e}')

        await self.async_update()

    async def async_update(self):
        """Retrieve the latest state."""
        LOG.debug(f'updating {self.unique_id}')

        try:
            value = await self._client.lipsync.get()
            if value is not None:
                self._attr_native_value = value
        except Exception as e:
            LOG.exception(f'could not update {self.unique_id}: {e}')

    async def async_set_native_value(self, value: float) -> None:
        """Set lipsync delay."""
        await self._client.lipsync.set(int(value))
        self.async_schedule_update_ha_state(force_refresh=True)


class McIntoshCenterTrimNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_native_min_value = -120
    _attr_native_max_value = 120
    _attr_native_step = 10
    _attr_mode = NumberMode.SLIDER
    _attr_icon = 'mdi:speaker'

    def __init__(self, config_entry: ConfigEntry, details: DeviceClientDetails) -> None:
        self._config_entry = config_entry
        self._details = details
        self._client = details.client

        model_id = config_entry.data[CONF_MODEL]
        self._attr_unique_id = f'{DOMAIN}_{model_id}_center_trim'.lower().replace(' ', '_')
        self._attr_name = 'Center Channel Trim'
        self._attr_native_unit_of_measurement = 'x0.1dB'
        self._attr_device_info = _get_device_info(config_entry)

    async def async_added_to_hass(self) -> None:
        await self.async_update()

    async def async_update(self):
        """Retrieve the latest state."""
        LOG.debug(f'updating {self.unique_id}')

        try:
            value = await self._client.channel_trim.get_center()
            if value is not None:
                self._attr_native_value = value
        except Exception as e:
            LOG.exception(f'could not update {self.unique_id}: {e}')

    async def async_set_native_value(self, value: float) -> None:
        """Set center channel trim level."""
        await self._client.channel_trim.set_center(int(value))
        self.async_schedule_update_ha_state(force_refresh=True)


class McIntoshLFETrimNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_native_min_value = -120
    _attr_native_max_value = 120
    _attr_native_step = 10
    _attr_mode = NumberMode.SLIDER
    _attr_icon = 'mdi:waveform'

    def __init__(self, config_entry: ConfigEntry, details: DeviceClientDetails) -> None:
        self._config_entry = config_entry
        self._details = details
        self._client = details.client

        model_id = config_entry.data[CONF_MODEL]
        self._attr_unique_id = f'{DOMAIN}_{model_id}_lfe_trim'.lower().replace(' ', '_')
        self._attr_name = 'LFE Channel Trim'
        self._attr_native_unit_of_measurement = 'x0.1dB'
        self._attr_device_info = _get_device_info(config_entry)

    async def async_added_to_hass(self) -> None:
        await self.async_update()

    async def async_update(self):
        """Retrieve the latest state."""
        LOG.debug(f'updating {self.unique_id}')

        try:
            value = await self._client.channel_trim.get_lfe()
            if value is not None:
                self._attr_native_value = value
        except Exception as e:
            LOG.exception(f'could not update {self.unique_id}: {e}')

    async def async_set_native_value(self, value: float) -> None:
        """Set LFE channel trim level."""
        await self._client.channel_trim.set_lfe(int(value))
        self.async_schedule_update_ha_state(force_refresh=True)


class McIntoshSurroundsTrimNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_native_min_value = -120
    _attr_native_max_value = 120
    _attr_native_step = 10
    _attr_mode = NumberMode.SLIDER
    _attr_icon = 'mdi:surround-sound'

    def __init__(self, config_entry: ConfigEntry, details: DeviceClientDetails) -> None:
        self._config_entry = config_entry
        self._details = details
        self._client = details.client

        model_id = config_entry.data[CONF_MODEL]
        self._attr_unique_id = f'{DOMAIN}_{model_id}_surrounds_trim'.lower().replace(' ', '_')
        self._attr_name = 'Surround Channels Trim'
        self._attr_native_unit_of_measurement = 'x0.1dB'
        self._attr_device_info = _get_device_info(config_entry)

    async def async_added_to_hass(self) -> None:
        await self.async_update()

    async def async_update(self):
        """Retrieve the latest state."""
        LOG.debug(f'updating {self.unique_id}')

        try:
            value = await self._client.channel_trim.get_surrounds()
            if value is not None:
                self._attr_native_value = value
        except Exception as e:
            LOG.exception(f'could not update {self.unique_id}: {e}')

    async def async_set_native_value(self, value: float) -> None:
        """Set surround channels trim level."""
        await self._client.channel_trim.set_surrounds(int(value))
        self.async_schedule_update_ha_state(force_refresh=True)


class McIntoshHeightTrimNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_native_min_value = -120
    _attr_native_max_value = 120
    _attr_native_step = 10
    _attr_mode = NumberMode.SLIDER
    _attr_icon = 'mdi:arrow-up-bold'

    def __init__(self, config_entry: ConfigEntry, details: DeviceClientDetails) -> None:
        self._config_entry = config_entry
        self._details = details
        self._client = details.client

        model_id = config_entry.data[CONF_MODEL]
        self._attr_unique_id = f'{DOMAIN}_{model_id}_height_trim'.lower().replace(' ', '_')
        self._attr_name = 'Height Channels Trim'
        self._attr_native_unit_of_measurement = 'x0.1dB'
        self._attr_device_info = _get_device_info(config_entry)

    async def async_added_to_hass(self) -> None:
        await self.async_update()

    async def async_update(self):
        """Retrieve the latest state."""
        LOG.debug(f'updating {self.unique_id}')

        try:
            value = await self._client.channel_trim.get_height()
            if value is not None:
                self._attr_native_value = value
        except Exception as e:
            LOG.exception(f'could not update {self.unique_id}: {e}')

    async def async_set_native_value(self, value: float) -> None:
        """Set height channels trim level."""
        await self._client.channel_trim.set_height(int(value))
        self.async_schedule_update_ha_state(force_refresh=True)
