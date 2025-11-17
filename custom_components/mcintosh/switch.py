"""Home Assistant McIntosh Switch Platform"""

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DeviceClientDetails
from .const import CONF_MODEL, DOMAIN
from .pymcintosh.models import get_model_config

LOG = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    if data := hass.data[DOMAIN][config_entry.entry_id]:
        entities = [McIntoshLoudnessSwitch(config_entry, data)]
        async_add_entities(new_entities=entities, update_before_add=True)
    else:
        LOG.error(
            f'missing pre-connected client for {config_entry}, cannot create switches'
        )


class McIntoshLoudnessSwitch(SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, config_entry: ConfigEntry, details: DeviceClientDetails) -> None:
        self._config_entry = config_entry
        self._details = details
        self._client = details.client

        model_id = config_entry.data[CONF_MODEL]
        model_config = get_model_config(model_id)
        manufacturer = 'McIntosh'
        model_name = model_config['name']

        self._attr_unique_id = f'{DOMAIN}_{model_id}_loudness'.lower().replace(' ', '_')
        self._attr_name = 'Loudness'
        self._attr_icon = 'mdi:volume-high'

        # device info to group with media player
        device_unique_id = f'{DOMAIN}_{model_id}'.lower().replace(' ', '_')
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_unique_id)},
            manufacturer=manufacturer,
            model=model_name,
            name=f'{manufacturer} {model_name}',
        )

    async def async_added_to_hass(self) -> None:
        """Turn on the dispatchers."""
        await self.async_update()

    async def async_update(self):
        """Retrieve the latest state."""
        LOG.debug(f'updating {self.unique_id}')

        try:
            is_on = await self._client.loudness.get()
            if is_on is not None:
                self._attr_is_on = is_on
        except Exception as e:
            LOG.exception(f'could not update {self.unique_id}: {e}')

    async def async_turn_on(self, **kwargs):
        """Turn loudness on."""
        await self._client.loudness.on()
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_turn_off(self, **kwargs):
        """Turn loudness off."""
        await self._client.loudness.off()
        self.async_schedule_update_ha_state(force_refresh=True)
