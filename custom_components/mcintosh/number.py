"""McIntosh Number platform."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Final

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MODEL, DOMAIN
from .coordinator import McIntoshCoordinator
from .pymcintosh.models import get_model_config

LOG = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class McIntoshNumberEntityDescription(NumberEntityDescription):
    """Describes McIntosh number entity."""

    data_key: str


TRIM_NUMBERS: Final[tuple[McIntoshNumberEntityDescription, ...]] = (
    McIntoshNumberEntityDescription(
        key='bass_trim',
        translation_key='bass_trim',
        native_min_value=-120,
        native_max_value=120,
        native_step=10,
        native_unit_of_measurement='x0.1dB',
        mode=NumberMode.SLIDER,
        icon='mdi:music-clef-bass',
        data_key='bass_trim',
    ),
    McIntoshNumberEntityDescription(
        key='treble_trim',
        translation_key='treble_trim',
        native_min_value=-120,
        native_max_value=120,
        native_step=10,
        native_unit_of_measurement='x0.1dB',
        mode=NumberMode.SLIDER,
        icon='mdi:music-clef-treble',
        data_key='treble_trim',
    ),
    McIntoshNumberEntityDescription(
        key='lipsync_delay',
        translation_key='lipsync_delay',
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement='ms',
        mode=NumberMode.BOX,
        icon='mdi:timer-outline',
        data_key='lipsync_delay',
    ),
    McIntoshNumberEntityDescription(
        key='center_trim',
        translation_key='center_channel_trim',
        native_min_value=-120,
        native_max_value=120,
        native_step=10,
        native_unit_of_measurement='x0.1dB',
        mode=NumberMode.SLIDER,
        icon='mdi:speaker',
        data_key='center_trim',
    ),
    McIntoshNumberEntityDescription(
        key='lfe_trim',
        translation_key='lfe_channel_trim',
        native_min_value=-120,
        native_max_value=120,
        native_step=10,
        native_unit_of_measurement='x0.1dB',
        mode=NumberMode.SLIDER,
        icon='mdi:waveform',
        data_key='lfe_trim',
    ),
    McIntoshNumberEntityDescription(
        key='surrounds_trim',
        translation_key='surround_channels_trim',
        native_min_value=-120,
        native_max_value=120,
        native_step=10,
        native_unit_of_measurement='x0.1dB',
        mode=NumberMode.SLIDER,
        icon='mdi:surround-sound',
        data_key='surrounds_trim',
    ),
    McIntoshNumberEntityDescription(
        key='height_trim',
        translation_key='height_channels_trim',
        native_min_value=-120,
        native_max_value=120,
        native_step=10,
        native_unit_of_measurement='x0.1dB',
        mode=NumberMode.SLIDER,
        icon='mdi:arrow-up-bold',
        data_key='height_trim',
    ),
)


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
    """Set up McIntosh number entities from config entry."""
    coordinator: McIntoshCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    model_id = config_entry.data[CONF_MODEL]
    device_info = _get_device_info(config_entry)

    entities: list[McIntoshNumberEntity] = [
        McIntoshNumberEntity(
            coordinator=coordinator,
            description=description,
            model_id=model_id,
            device_info=device_info,
        )
        for description in TRIM_NUMBERS
    ]

    async_add_entities(entities)


class McIntoshNumberEntity(CoordinatorEntity[McIntoshCoordinator], NumberEntity):
    """Representation of a McIntosh number entity."""

    _attr_has_entity_name = True
    entity_description: McIntoshNumberEntityDescription

    def __init__(
        self,
        coordinator: McIntoshCoordinator,
        description: McIntoshNumberEntityDescription,
        model_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._model_id = model_id

        self._attr_unique_id = f'{DOMAIN}_{model_id}_{description.key}'.lower().replace(' ', '_')
        self._attr_device_info = device_info

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data:
            data = self.coordinator.data
            value = getattr(data, self.entity_description.data_key, None)
            if value is not None:
                self._attr_native_value = value

            # update lipsync range if available
            if self.entity_description.key == 'lipsync_delay':
                if data.lipsync_min is not None:
                    self._attr_native_min_value = data.lipsync_min
                if data.lipsync_max is not None:
                    self._attr_native_max_value = data.lipsync_max

        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        int_value = int(value)
        key = self.entity_description.key

        if key == 'bass_trim':
            await self.coordinator.client.bass_treble.set_bass(int_value)
        elif key == 'treble_trim':
            await self.coordinator.client.bass_treble.set_treble(int_value)
        elif key == 'lipsync_delay':
            await self.coordinator.client.lipsync.set(int_value)
        elif key == 'center_trim':
            await self.coordinator.client.channel_trim.set_center(int_value)
        elif key == 'lfe_trim':
            await self.coordinator.client.channel_trim.set_lfe(int_value)
        elif key == 'surrounds_trim':
            await self.coordinator.client.channel_trim.set_surrounds(int_value)
        elif key == 'height_trim':
            await self.coordinator.client.channel_trim.set_height(int_value)

        await self.coordinator.async_request_refresh()
