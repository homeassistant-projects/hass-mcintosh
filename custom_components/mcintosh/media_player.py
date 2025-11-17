"""Home Assistant McIntosh Media Player"""

import logging
from typing import Final

from .pymcintosh.models import get_model_config, SOURCES

from homeassistant import core
from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
)
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DeviceClientDetails
from .const import CONF_MODEL, CONF_SOURCES, DOMAIN

LOG = logging.getLogger(__name__)

MINUTES: Final = 60
MAX_VOLUME = 99  # McIntosh volume range is 0-99


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    if data := hass.data[DOMAIN][config_entry.entry_id]:
        entities = [McIntoshMediaPlayer(config_entry, data)]
        async_add_entities(new_entities=entities, update_before_add=True)
    else:
        LOG.error(
            f'Missing pre-connected client for {config_entry}, cannot create MediaPlayer'
        )


@core.callback
def _get_sources_from_dict(data):
    sources_config = data[CONF_SOURCES]
    source_id_name = {int(index): name for index, name in sources_config.items()}
    source_name_id = {v: k for k, v in source_id_name.items()}
    source_names = sorted(source_name_id.keys(), key=lambda v: source_name_id[v])
    return [source_id_name, source_name_id, source_names]


@core.callback
def _get_sources(config_entry):
    if CONF_SOURCES in config_entry.options:
        data = config_entry.options
    else:
        data = config_entry.data
    return _get_sources_from_dict(data)


class McIntoshMediaPlayer(MediaPlayerEntity):
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )
    _attr_has_entity_name = True

    def __init__(self, config_entry: ConfigEntry, details: DeviceClientDetails) -> None:
        self._config_entry = config_entry
        self._details = details
        self._client = details.client
        self._model_id = config_entry.data[CONF_MODEL]

        # get model configuration
        self._model_config = get_model_config(self._model_id)

        self._attr_unique_id = f'{DOMAIN}_{self._model_id}'.lower().replace(' ', '_')

        # device information
        manufacturer = 'McIntosh'
        model_name = self._model_config['name']

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            manufacturer=manufacturer,
            model=model_name,
            name=f'{manufacturer} {model_name}',
            sw_version='Unknown',
        )

        # setup source list from config or use default SOURCES
        if CONF_SOURCES in config_entry.data:
            source_id_name, source_name_id, source_names = _get_sources(config_entry)
            self._source_id_to_name = source_id_name
            self._source_name_to_id = source_name_id
            self._attr_source_list = source_names
        else:
            # use default sources from pymcintosh
            self._source_id_to_name = SOURCES
            self._source_name_to_id = {v: k for k, v in SOURCES.items()}
            self._attr_source_list = sorted(
                self._source_name_to_id.keys(),
                key=lambda v: self._source_name_to_id[v]
            )

    async def async_added_to_hass(self) -> None:
        """Turn on the dispatchers."""
        await self._initialize()

    async def _initialize(self) -> None:
        """Initialize connection dependent variables."""
        LOG.debug(f'Connected to {self._model_id} / {self._unique_id}')
        await self.async_update()

    async def async_update(self):
        """Retrieve the latest state."""
        LOG.debug(f'Updating {self.unique_id}')

        try:
            # get power state
            power = await self._client.power.get()
            if power is None:
                LOG.warning(f'Could not get power state for {self.unique_id}')
                return

            self._attr_state = MediaPlayerState.ON if power else MediaPlayerState.OFF

            # only query other state if device is on
            if power:
                # get volume
                volume = await self._client.volume.get()
                if volume is not None:
                    self._attr_volume_level = volume / MAX_VOLUME

                # get mute state
                mute = await self._client.mute.get()
                if mute is not None:
                    self._attr_is_volume_muted = mute

                # get current source
                source_info = await self._client.source.get()
                if source_info:
                    source_id = source_info.get('source')
                    self._attr_source = self._source_id_to_name.get(source_id)

        except Exception as e:
            LOG.exception(f'Could not update {self.unique_id}: {e}')

    async def async_select_source(self, source):
        """Select input source."""
        if source not in self._source_name_to_id:
            LOG.warning(
                f"Selected source '{source}' not valid for {self.unique_id}, ignoring! Sources: {self._source_name_to_id}"
            )
            return

        source_id = self._source_name_to_id[source]
        await self._client.source.set(source_id)
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_turn_on(self):
        """Turn the media player on."""
        await self._client.power.on()
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_turn_off(self):
        """Turn the media player off."""
        await self._client.power.off()
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_mute_volume(self, mute):
        """Mute (true) or unmute (false) media player."""
        if mute:
            await self._client.mute.on()
        else:
            await self._client.mute.off()
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_set_volume_level(self, volume):
        """Set volume level, range 0-1.0"""
        scaled_volume = int(volume * MAX_VOLUME)
        LOG.debug(f'Setting volume to {scaled_volume} (HA volume {volume})')
        await self._client.volume.set(scaled_volume)
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_volume_up(self):
        """Volume up the media player."""
        await self._client.volume.up()
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_volume_down(self):
        """Volume down the media player."""
        await self._client.volume.down()
        self.async_schedule_update_ha_state(force_refresh=True)

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        if self.state is MediaPlayerState.OFF or self.is_volume_muted:
            return 'mdi:speaker-off'
        return 'mdi:speaker'
