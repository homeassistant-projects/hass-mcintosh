"""DataUpdateCoordinator for McIntosh integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .pymcintosh import McIntoshAsync

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

LOG = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)


@dataclass
class McIntoshData:
    """Data class holding McIntosh device state."""

    power: bool = False
    volume: int = 0
    muted: bool = False
    source_id: int | None = None
    source_name: str | None = None
    loudness: bool = False
    bass_trim: int = 0
    treble_trim: int = 0
    lipsync_delay: int = 0
    lipsync_min: int = 0
    lipsync_max: int = 100
    center_trim: int = 0
    lfe_trim: int = 0
    surrounds_trim: int = 0
    height_trim: int = 0


class McIntoshCoordinator(DataUpdateCoordinator[McIntoshData]):
    """Coordinator to manage data updates from McIntosh device."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: McIntoshAsync,
        model_id: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOG,
            name=f'McIntosh {model_id}',
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client
        self.model_id = model_id
        self._lipsync_range_fetched = False

    async def _async_update_data(self) -> McIntoshData:
        """Fetch data from the device."""
        try:
            data = McIntoshData()

            # get power state first
            power = await self.client.power.get()
            if power is None:
                raise UpdateFailed(f'Could not get power state from {self.model_id}')

            data.power = power

            # only query other state if device is on
            if power:
                # volume
                volume = await self.client.volume.get()
                if volume is not None:
                    data.volume = volume

                # mute
                mute = await self.client.mute.get()
                if mute is not None:
                    data.muted = mute

                # source
                source_info = await self.client.source.get()
                if source_info:
                    data.source_id = source_info.get('source')
                    data.source_name = source_info.get('name')

                # loudness
                loudness = await self.client.loudness.get()
                if loudness is not None:
                    data.loudness = loudness

                # bass/treble
                bass = await self.client.bass_treble.get_bass()
                if bass is not None:
                    data.bass_trim = bass

                treble = await self.client.bass_treble.get_treble()
                if treble is not None:
                    data.treble_trim = treble

                # lipsync
                lipsync = await self.client.lipsync.get()
                if lipsync is not None:
                    data.lipsync_delay = lipsync

                # fetch lipsync range once
                if not self._lipsync_range_fetched:
                    lipsync_range = await self.client.lipsync.get_range()
                    if lipsync_range:
                        data.lipsync_min = lipsync_range['min']
                        data.lipsync_max = lipsync_range['max']
                        self._lipsync_range_fetched = True

                # channel trims
                center = await self.client.channel_trim.get_center()
                if center is not None:
                    data.center_trim = center

                lfe = await self.client.channel_trim.get_lfe()
                if lfe is not None:
                    data.lfe_trim = lfe

                surrounds = await self.client.channel_trim.get_surrounds()
                if surrounds is not None:
                    data.surrounds_trim = surrounds

                height = await self.client.channel_trim.get_height()
                if height is not None:
                    data.height_trim = height

            return data

        except Exception as err:
            raise UpdateFailed(f'Error communicating with {self.model_id}: {err}') from err
