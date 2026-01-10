"""McIntosh Switch platform."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MODEL, DOMAIN
from .coordinator import McIntoshCoordinator
from .pymcintosh.models import get_model_config

LOG = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up McIntosh switch from config entry."""
    coordinator: McIntoshCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([McIntoshLoudnessSwitch(coordinator, config_entry)])


class McIntoshLoudnessSwitch(CoordinatorEntity[McIntoshCoordinator], SwitchEntity):
    """Representation of McIntosh loudness switch."""

    _attr_has_entity_name = True
    _attr_translation_key = 'loudness'
    _attr_icon = 'mdi:volume-high'

    def __init__(
        self,
        coordinator: McIntoshCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._config_entry = config_entry

        model_id = config_entry.data[CONF_MODEL]
        model_config = get_model_config(model_id)
        manufacturer = 'McIntosh'
        model_name = model_config['name']

        self._attr_unique_id = f'{DOMAIN}_{model_id}_loudness'.lower().replace(' ', '_')

        # device info to group with media player
        device_unique_id = f'{DOMAIN}_{model_id}'.lower().replace(' ', '_')
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_unique_id)},
            manufacturer=manufacturer,
            model=model_name,
            name=f'{manufacturer} {model_name}',
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data:
            self._attr_is_on = self.coordinator.data.loudness
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn loudness on."""
        await self.coordinator.client.loudness.on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn loudness off."""
        await self.coordinator.client.loudness.off()
        await self.coordinator.async_request_refresh()
