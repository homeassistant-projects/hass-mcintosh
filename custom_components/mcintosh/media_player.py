"""McIntosh Media Player platform."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MODEL, CONF_SOURCES, DOMAIN
from .coordinator import McIntoshCoordinator
from .pymcintosh.models import SOURCES, get_model_config

LOG = logging.getLogger(__name__)

MAX_VOLUME: Final = 99  # McIntosh volume range is 0-99


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up McIntosh media player from config entry."""
    coordinator: McIntoshCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([McIntoshMediaPlayer(coordinator, config_entry)])


def _get_sources_from_config(config_entry: ConfigEntry) -> tuple[dict[int, str], dict[str, int], list[str]]:
    """Get source mappings from config entry."""
    if CONF_SOURCES in config_entry.options:
        sources_config = config_entry.options[CONF_SOURCES]
    elif CONF_SOURCES in config_entry.data:
        sources_config = config_entry.data[CONF_SOURCES]
    else:
        # use default sources
        source_id_name = SOURCES
        source_name_id = {v: k for k, v in SOURCES.items()}
        source_names = sorted(source_name_id.keys(), key=lambda v: source_name_id[v])
        return source_id_name, source_name_id, source_names

    source_id_name = {int(idx): name for idx, name in sources_config.items()}
    source_name_id = {v: k for k, v in source_id_name.items()}
    source_names = sorted(source_name_id.keys(), key=lambda v: source_name_id[v])
    return source_id_name, source_name_id, source_names


class McIntoshMediaPlayer(CoordinatorEntity[McIntoshCoordinator], MediaPlayerEntity):
    """Representation of a McIntosh media player."""

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
    _attr_name = None  # use device name

    def __init__(
        self,
        coordinator: McIntoshCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the media player."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._model_id = config_entry.data[CONF_MODEL]
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
        )

        # setup source list
        self._source_id_to_name, self._source_name_to_id, self._attr_source_list = (
            _get_sources_from_config(config_entry)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data:
            data = self.coordinator.data
            self._attr_state = MediaPlayerState.ON if data.power else MediaPlayerState.OFF

            if data.power:
                self._attr_volume_level = data.volume / MAX_VOLUME
                self._attr_is_volume_muted = data.muted
                if data.source_id is not None:
                    self._attr_source = self._source_id_to_name.get(data.source_id)

        self.async_write_ha_state()

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        if source not in self._source_name_to_id:
            LOG.warning(f"Source '{source}' not valid, ignoring")
            return

        source_id = self._source_name_to_id[source]
        await self.coordinator.client.source.set(source_id)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        await self.coordinator.client.power.on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        await self.coordinator.client.power.off()
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute media player."""
        if mute:
            await self.coordinator.client.mute.on()
        else:
            await self.coordinator.client.mute.off()
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0-1.0."""
        scaled_volume = int(volume * MAX_VOLUME)
        LOG.debug(f'Setting volume to {scaled_volume} (HA volume {volume})')
        await self.coordinator.client.volume.set(scaled_volume)
        await self.coordinator.async_request_refresh()

    async def async_volume_up(self) -> None:
        """Volume up the media player."""
        await self.coordinator.client.volume.up()
        await self.coordinator.async_request_refresh()

    async def async_volume_down(self) -> None:
        """Volume down the media player."""
        await self.coordinator.client.volume.down()
        await self.coordinator.async_request_refresh()

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        if self.state is MediaPlayerState.OFF or self.is_volume_muted:
            return 'mdi:speaker-off'
        return 'mdi:speaker'
