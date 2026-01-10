"""Python library for controlling McIntosh MX160/MX170/MX180 processors."""

from __future__ import annotations

import logging
from threading import RLock
from typing import Any

import serial

from .models import (
    get_model_config,
    SUPPORTED_MODELS,
    COMMAND_EOL,
    RESPONSE_EOL,
    SOURCES,
)
from .protocol import async_get_protocol

__version__ = '0.1.0'

LOG = logging.getLogger(__name__)


class PowerControl:
    """Power control interface."""

    def __init__(self, client):
        self._client = client

    def on(self):
        """Turn system power on."""
        return self._client._send_command('!PON')

    def off(self):
        """Turn system power off."""
        return self._client._send_command('!POFF')

    def toggle(self):
        """Toggle system power."""
        return self._client._send_command('!PTOGGLE')

    def get(self) -> bool | None:
        """Get power status (True=on, False=off)."""
        response = self._client._send_command('!POWER?')
        if response and '!POWER(' in response:
            # extract power state: !POWER(1) or !POWER(0)
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class VolumeControl:
    """Volume control interface."""

    def __init__(self, client):
        self._client = client

    def set(self, level: int):
        """Set volume level (0-99)."""
        level = max(0, min(99, level))
        return self._client._send_command(f'!VOL({level})')

    def up(self, amount: int | None = None):
        """Increase volume (optionally by specific amount)."""
        if amount:
            return self._client._send_command(f'!VOL+({amount})')
        return self._client._send_command('!VOL+')

    def down(self, amount: int | None = None):
        """Decrease volume (optionally by specific amount)."""
        if amount:
            return self._client._send_command(f'!VOL-({amount})')
        return self._client._send_command('!VOL-')

    def get(self) -> int | None:
        """Get current volume level."""
        response = self._client._send_command('!VOL?')
        if response and '!VOL(' in response:
            vol = response.split('(')[1].split(')')[0]
            return int(vol)
        return None

    def max_vol(self) -> int | None:
        """Get maximum volume setting (MX170/MX180 only)."""
        if not self._client._model_config.get('supports_max_volume_query'):
            LOG.warning(f'{self._client._model_id} does not support max volume query')
            return None
        response = self._client._send_command('!MAXVOL?')
        if response and '!MAXVOL(' in response:
            max_vol = response.split('(')[1].split(')')[0]
            return int(max_vol)
        return None


class MuteControl:
    """Mute control interface."""

    def __init__(self, client):
        self._client = client

    def on(self):
        """Mute on."""
        return self._client._send_command('!MUTEON')

    def off(self):
        """Mute off."""
        return self._client._send_command('!MUTEOFF')

    def toggle(self):
        """Toggle mute."""
        return self._client._send_command('!MUTE')

    def get(self) -> bool | None:
        """Get mute status (True=muted, False=unmuted)."""
        response = self._client._send_command('!MUTE?')
        if response and '!MUTE(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class SourceControl:
    """Source/input control interface."""

    def __init__(self, client):
        self._client = client

    def set(self, source: int):
        """Set source input (0-25)."""
        if source not in SOURCES:
            LOG.warning(f'Invalid source {source}, valid range: 0-25')
        return self._client._send_command(f'!SRC({source})')

    def get(self) -> dict[str, Any | None]:
        """Get current source info."""
        response = self._client._send_command('!SRC?')
        if response and '!SRC(' in response:
            # parse: !SRC(1) "HDMI 2"
            parts = response.split('(')[1].split(')')
            source_num = int(parts[0])
            name = parts[1].strip().strip('"') if len(parts) > 1 else SOURCES.get(source_num, '')
            return {'source': source_num, 'name': name}
        return None

    def next(self):
        """Select next source."""
        return self._client._send_command('!SRC+')

    def previous(self):
        """Select previous source."""
        return self._client._send_command('!SRC-')

    def info(self, source: int) -> dict[str, Any | None]:
        """Get info for specific source."""
        response = self._client._send_command(f'!SRC({source})?')
        if response and '!SRC(' in response:
            parts = response.split('(')[1].split(')')
            source_num = int(parts[0])
            name = parts[1].strip().strip('"') if len(parts) > 1 else ''
            return {'source': source_num, 'name': name}
        return None


class Zone2Control:
    """Zone 2 control interface."""

    def __init__(self, client):
        self._client = client
        self.power = Zone2PowerControl(client)
        self.volume = Zone2VolumeControl(client)
        self.mute = Zone2MuteControl(client)
        self.source = Zone2SourceControl(client)


class Zone2PowerControl:
    """Zone 2 power control."""

    def __init__(self, client):
        self._client = client

    def on(self):
        """Turn Zone 2 power on."""
        return self._client._send_command('!POWERONZONE2')

    def off(self):
        """Turn Zone 2 power off."""
        return self._client._send_command('!POWEROFFZONE2')

    def toggle(self):
        """Toggle Zone 2 power."""
        return self._client._send_command('!ZPTOGGLE')

    def get(self) -> bool | None:
        """Get Zone 2 power status."""
        response = self._client._send_command('!POWERZONE2?')
        if response and '!POWER(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class Zone2VolumeControl:
    """Zone 2 volume control."""

    def __init__(self, client):
        self._client = client

    def set(self, level: int):
        """Set Zone 2 volume."""
        level = max(0, min(99, level))
        return self._client._send_command(f'!ZVOL({level})')

    def up(self, amount: int | None = None):
        """Increase Zone 2 volume."""
        if amount:
            return self._client._send_command(f'!ZVOL+({amount})')
        return self._client._send_command('!ZVOL+')

    def down(self, amount: int | None = None):
        """Decrease Zone 2 volume."""
        if amount:
            return self._client._send_command(f'!ZVOL-({amount})')
        return self._client._send_command('!ZVOL-')

    def get(self) -> int | None:
        """Get Zone 2 volume level."""
        response = self._client._send_command('!ZVOL?')
        if response and '!ZVOL(' in response:
            vol = response.split('(')[1].split(')')[0]
            return int(vol)
        return None


class Zone2MuteControl:
    """Zone 2 mute control."""

    def __init__(self, client):
        self._client = client

    def on(self):
        """Zone 2 mute on."""
        return self._client._send_command('!ZMUTEON')

    def off(self):
        """Zone 2 mute off."""
        return self._client._send_command('!ZMUTEOFF')

    def toggle(self):
        """Toggle Zone 2 mute."""
        return self._client._send_command('!ZMUTE')

    def get(self) -> bool | None:
        """Get Zone 2 mute status."""
        response = self._client._send_command('!ZMUTE?')
        if response and '!ZMUTE(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class Zone2SourceControl:
    """Zone 2 source control."""

    def __init__(self, client):
        self._client = client

    def set(self, source: int):
        """Set Zone 2 source."""
        return self._client._send_command(f'!ZSRC({source})')

    def get(self) -> dict[str, Any | None]:
        """Get Zone 2 current source."""
        response = self._client._send_command('!ZSRC?')
        if response and '!ZSRC(' in response:
            parts = response.split('(')[1].split(')')
            source_num = int(parts[0])
            name = parts[1].strip().strip('"') if len(parts) > 1 else ''
            return {'source': source_num, 'name': name}
        return None

    def next(self):
        """Select next Zone 2 source."""
        return self._client._send_command('!ZSRC+')

    def previous(self):
        """Select previous Zone 2 source."""
        return self._client._send_command('!ZSRC-')


class BassTrebleControl:
    """Bass and treble trim controls."""

    def __init__(self, client):
        self._client = client

    def get_bass(self) -> int | None:
        """Get bass level trim (10 = 1dB)."""
        response = self._client._send_command('!TRIMBASS?')
        if response and '!TRIMBASS(' in response:
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None

    def set_bass(self, level: int):
        """Set bass level trim (10 = 1dB)."""
        return self._client._send_command(f'!TRIMBASS({level})')

    def bass_up(self):
        """Increase bass level trim."""
        return self._client._send_command('!TRIMBASS+')

    def bass_down(self):
        """Decrease bass level trim."""
        return self._client._send_command('!TRIMBASS-')

    def get_treble(self) -> int | None:
        """Get treble level trim (10 = 1dB, -120 to +120)."""
        response = self._client._send_command('!TRIMTREB?')
        if response and ('!TRIMTREB(' in response or '!TRIMTREBLE(' in response):
            # handle both MX160 (!TRIMTREB) and MX170+ (!TRIMTREBLE) responses
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None

    def set_treble(self, level: int):
        """Set treble level trim (10 = 1dB, -120 to +120)."""
        level = max(-120, min(120, level))
        return self._client._send_command(f'!TRIMTREB({level})')

    def treble_up(self):
        """Increase treble level trim."""
        return self._client._send_command('!TRIMTREB+')

    def treble_down(self):
        """Decrease treble level trim."""
        return self._client._send_command('!TRIMTREB-')


class LoudnessControl:
    """Loudness control."""

    def __init__(self, client):
        self._client = client

    def on(self):
        """Turn loudness on."""
        return self._client._send_command('!LOUDNESS(1)')

    def off(self):
        """Turn loudness off."""
        return self._client._send_command('!LOUDNESS(0)')

    def get(self) -> bool | None:
        """Get loudness status (True=on, False=off)."""
        response = self._client._send_command('!LOUDNESS?')
        if response and '!LOUDNESS(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class LipsyncControl:
    """Lipsync delay control."""

    def __init__(self, client):
        self._client = client

    def get(self) -> int | None:
        """Get lipsync delay value."""
        response = self._client._send_command('!LIPSYNC?')
        if response and '!LIPSYNC(' in response:
            value = response.split('(')[1].split(')')[0]
            return int(value)
        return None

    def set(self, value: int):
        """Set lipsync delay value."""
        return self._client._send_command(f'!LIPSYNC({value})')

    def up(self):
        """Increase lipsync delay."""
        return self._client._send_command('!LIPSYNC+')

    def down(self):
        """Decrease lipsync delay."""
        return self._client._send_command('!LIPSYNC-')

    def get_range(self) -> dict[str, int | None]:
        """Get lipsync range (min/max values)."""
        response = self._client._send_command('!LIPSYNCRANGE?')
        if response and '!LIPSYNCRANGE(' in response:
            # parse: !LIPSYNCRANGE(min,max)
            values = response.split('(')[1].split(')')[0].split(',')
            if len(values) == 2:
                return {'min': int(values[0]), 'max': int(values[1])}
        return None


class ChannelTrimControl:
    """Channel level trim controls (center, lfe, surrounds, height)."""

    def __init__(self, client):
        self._client = client

    def get_center(self) -> int | None:
        """Get center channel level trim (10 = 1dB)."""
        response = self._client._send_command('!TRIMCENTER?')
        if response and '!TRIMCENTER(' in response:
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None

    def set_center(self, level: int):
        """Set center channel level trim (10 = 1dB)."""
        return self._client._send_command(f'!TRIMCENTER({level})')

    def center_up(self):
        """Increase center channel level trim."""
        return self._client._send_command('!TRIMCENTER+')

    def center_down(self):
        """Decrease center channel level trim."""
        return self._client._send_command('!TRIMCENTER-')

    def get_lfe(self) -> int | None:
        """Get LFE channel level trim (10 = 1dB)."""
        response = self._client._send_command('!TRIMLFE?')
        if response and '!TRIMLFE(' in response:
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None

    def set_lfe(self, level: int):
        """Set LFE channel level trim (10 = 1dB)."""
        return self._client._send_command(f'!TRIMLFE({level})')

    def lfe_up(self):
        """Increase LFE channel level trim."""
        return self._client._send_command('!TRIMLFE+')

    def lfe_down(self):
        """Decrease LFE channel level trim."""
        return self._client._send_command('!TRIMLFE-')

    def get_surrounds(self) -> int | None:
        """Get surround channels level trim (10 = 1dB)."""
        response = self._client._send_command('!TRIMSURRS?')
        if response and '!TRIMSURRS(' in response:
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None

    def set_surrounds(self, level: int):
        """Set surround channels level trim (10 = 1dB)."""
        return self._client._send_command(f'!TRIMSURRS({level})')

    def surrounds_up(self):
        """Increase surround channels level trim."""
        return self._client._send_command('!TRIMSURRS+')

    def surrounds_down(self):
        """Decrease surround channels level trim."""
        return self._client._send_command('!TRIMSURRS-')

    def get_height(self) -> int | None:
        """Get height channels level trim (10 = 1dB)."""
        response = self._client._send_command('!TRIMHEIGHT?')
        if response and '!TRIMHEIGHT(' in response:
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None

    def set_height(self, level: int):
        """Set height channels level trim (10 = 1dB)."""
        return self._client._send_command(f'!TRIMHEIGHT({level})')

    def height_up(self):
        """Increase height channels level trim."""
        return self._client._send_command('!TRIMHEIGHT+')

    def height_down(self):
        """Decrease height channels level trim."""
        return self._client._send_command('!TRIMHEIGHT-')


class DeviceControl:
    """Device info and utility commands."""

    def __init__(self, client):
        self._client = client

    def name(self) -> str | None:
        """Get device name (e.g. MX160)."""
        response = self._client._send_command('!DEVICE?')
        if response and '!DEVICE(' in response:
            return response.split('(')[1].split(')')[0]
        return None

    def ping(self) -> bool:
        """Ping device (returns True if responds with PONG)."""
        response = self._client._send_command('!PING?')
        return response == '!PONG'


def get_mcintosh(model_id: str, port_url: str, **serial_config_overrides) -> 'McIntoshSync':
    """
    Get synchronous McIntosh controller.

    Args:
        model_id: Model identifier (mx160, mx170, mx180)
        port_url: Serial port or socket URL (e.g. '/dev/ttyUSB0', 'socket://192.168.1.100:84')
        **serial_config_overrides: Override serial config (e.g. baudrate=9600)

    Returns:
        Synchronous McIntosh controller instance
    """
    if model_id not in SUPPORTED_MODELS:
        LOG.error(f"Unsupported model '{model_id}'. Supported: {SUPPORTED_MODELS}")
        return None

    return McIntoshSync(model_id, port_url, serial_config_overrides)


async def async_get_mcintosh(
    model_id: str, port_url: str, loop, **serial_config_overrides
) -> 'McIntoshAsync':
    """
    Get asynchronous McIntosh controller.

    Args:
        model_id: Model identifier (mx160, mx170, mx180)
        port_url: Serial port or socket URL
        loop: asyncio event loop
        **serial_config_overrides: Override serial config

    Returns:
        Asynchronous McIntosh controller instance
    """
    if model_id not in SUPPORTED_MODELS:
        LOG.error(f"Unsupported model '{model_id}'. Supported: {SUPPORTED_MODELS}")
        return None

    model_config = get_model_config(model_id)
    serial_config = model_config['rs232'].copy()
    if serial_config_overrides:
        LOG.debug(f'Overriding serial config: {serial_config_overrides}')
        serial_config.update(serial_config_overrides)

    min_time_between_commands = model_config['min_time_between_commands']

    protocol = await async_get_protocol(
        port_url, min_time_between_commands, RESPONSE_EOL, serial_config, loop
    )

    client = McIntoshAsync(model_id, model_config, protocol)

    # send connection init command if specified
    if init_cmd := model_config.get('connection_init'):
        await client._send_command(init_cmd)

    return client


class McIntoshSync:
    """Synchronous McIntosh controller."""

    def __init__(self, model_id: str, port_url: str, serial_config_overrides: dict):
        self._model_id = model_id
        self._model_config = get_model_config(model_id)

        # setup serial config
        serial_config = self._model_config['rs232'].copy()
        if serial_config_overrides:
            LOG.debug(f'Overriding serial config: {serial_config_overrides}')
            serial_config.update(serial_config_overrides)

        self._port = serial.serial_for_url(port_url, **serial_config)
        self._lock = RLock()

        # create control interfaces
        self.power = PowerControl(self)
        self.volume = VolumeControl(self)
        self.mute = MuteControl(self)
        self.source = SourceControl(self)
        self.zone_2 = Zone2Control(self)
        self.bass_treble = BassTrebleControl(self)
        self.loudness = LoudnessControl(self)
        self.lipsync = LipsyncControl(self)
        self.channel_trim = ChannelTrimControl(self)
        self.device = DeviceControl(self)

        # send connection init if specified
        if init_cmd := self._model_config.get('connection_init'):
            self._send_command(init_cmd)

    def _send_command(self, command: str) -> str | None:
        """Send command and return response."""
        with self._lock:
            # clear buffers
            self._port.reset_output_buffer()
            self._port.reset_input_buffer()

            # build request
            request = (command + COMMAND_EOL).encode('ascii')
            LOG.debug(f'Sending: {request}')

            # send
            self._port.write(request)
            self._port.flush()

            # read response
            result = bytearray()
            eol_bytes = RESPONSE_EOL.encode('ascii')

            while True:
                c = self._port.read(1)
                if not c:
                    LOG.warning(f'Timeout waiting for response to {command}')
                    raise serial.SerialTimeoutException(
                        f'Connection timed out! Last received: {bytes(result)}'
                    )

                result += c
                if result.endswith(eol_bytes):
                    break

            response = bytes(result).decode('ascii').strip()
            LOG.debug(f'Received: {response}')
            return response


class McIntoshAsync:
    """Asynchronous McIntosh controller."""

    def __init__(self, model_id: str, model_config: dict, protocol):
        self._model_id = model_id
        self._model_config = model_config
        self._protocol = protocol

        # create control interfaces
        self.power = AsyncPowerControl(self)
        self.volume = AsyncVolumeControl(self)
        self.mute = AsyncMuteControl(self)
        self.source = AsyncSourceControl(self)
        self.zone_2 = AsyncZone2Control(self)
        self.bass_treble = AsyncBassTrebleControl(self)
        self.loudness = AsyncLoudnessControl(self)
        self.lipsync = AsyncLipsyncControl(self)
        self.channel_trim = AsyncChannelTrimControl(self)
        self.device = AsyncDeviceControl(self)

    async def _send_command(self, command: str) -> str | None:
        """Send command and return response."""
        request = (command + COMMAND_EOL).encode('ascii')
        return await self._protocol.send(request)


# async versions of control classes
class AsyncPowerControl(PowerControl):
    async def on(self):
        return await self._client._send_command('!PON')

    async def off(self):
        return await self._client._send_command('!POFF')

    async def toggle(self):
        return await self._client._send_command('!PTOGGLE')

    async def get(self) -> bool | None:
        response = await self._client._send_command('!POWER?')
        if response and '!POWER(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class AsyncVolumeControl(VolumeControl):
    async def set(self, level: int):
        level = max(0, min(99, level))
        return await self._client._send_command(f'!VOL({level})')

    async def up(self, amount: int | None = None):
        if amount:
            return await self._client._send_command(f'!VOL+({amount})')
        return await self._client._send_command('!VOL+')

    async def down(self, amount: int | None = None):
        if amount:
            return await self._client._send_command(f'!VOL-({amount})')
        return await self._client._send_command('!VOL-')

    async def get(self) -> int | None:
        response = await self._client._send_command('!VOL?')
        if response and '!VOL(' in response:
            vol = response.split('(')[1].split(')')[0]
            return int(vol)
        return None

    async def max_vol(self) -> int | None:
        if not self._client._model_config.get('supports_max_volume_query'):
            LOG.warning(f'{self._client._model_id} does not support max volume query')
            return None
        response = await self._client._send_command('!MAXVOL?')
        if response and '!MAXVOL(' in response:
            max_vol = response.split('(')[1].split(')')[0]
            return int(max_vol)
        return None


class AsyncMuteControl(MuteControl):
    async def on(self):
        return await self._client._send_command('!MUTEON')

    async def off(self):
        return await self._client._send_command('!MUTEOFF')

    async def toggle(self):
        return await self._client._send_command('!MUTE')

    async def get(self) -> bool | None:
        response = await self._client._send_command('!MUTE?')
        if response and '!MUTE(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class AsyncSourceControl(SourceControl):
    async def set(self, source: int):
        if source not in SOURCES:
            LOG.warning(f'Invalid source {source}, valid range: 0-25')
        return await self._client._send_command(f'!SRC({source})')

    async def get(self) -> dict[str, Any | None]:
        response = await self._client._send_command('!SRC?')
        if response and '!SRC(' in response:
            parts = response.split('(')[1].split(')')
            source_num = int(parts[0])
            name = parts[1].strip().strip('"') if len(parts) > 1 else SOURCES.get(source_num, '')
            return {'source': source_num, 'name': name}
        return None

    async def next(self):
        return await self._client._send_command('!SRC+')

    async def previous(self):
        return await self._client._send_command('!SRC-')

    async def info(self, source: int) -> dict[str, Any | None]:
        response = await self._client._send_command(f'!SRC({source})?')
        if response and '!SRC(' in response:
            parts = response.split('(')[1].split(')')
            source_num = int(parts[0])
            name = parts[1].strip().strip('"') if len(parts) > 1 else ''
            return {'source': source_num, 'name': name}
        return None


class AsyncZone2Control:
    """Async Zone 2 control interface."""

    def __init__(self, client):
        self._client = client
        self.power = AsyncZone2PowerControl(client)
        self.volume = AsyncZone2VolumeControl(client)
        self.mute = AsyncZone2MuteControl(client)
        self.source = AsyncZone2SourceControl(client)


class AsyncZone2PowerControl(Zone2PowerControl):
    async def on(self):
        return await self._client._send_command('!POWERONZONE2')

    async def off(self):
        return await self._client._send_command('!POWEROFFZONE2')

    async def toggle(self):
        return await self._client._send_command('!ZPTOGGLE')

    async def get(self) -> bool | None:
        response = await self._client._send_command('!POWERZONE2?')
        if response and '!POWER(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class AsyncZone2VolumeControl(Zone2VolumeControl):
    async def set(self, level: int):
        level = max(0, min(99, level))
        return await self._client._send_command(f'!ZVOL({level})')

    async def up(self, amount: int | None = None):
        if amount:
            return await self._client._send_command(f'!ZVOL+({amount})')
        return await self._client._send_command('!ZVOL+')

    async def down(self, amount: int | None = None):
        if amount:
            return await self._client._send_command(f'!ZVOL-({amount})')
        return await self._client._send_command('!ZVOL-')

    async def get(self) -> int | None:
        response = await self._client._send_command('!ZVOL?')
        if response and '!ZVOL(' in response:
            vol = response.split('(')[1].split(')')[0]
            return int(vol)
        return None


class AsyncZone2MuteControl(Zone2MuteControl):
    async def on(self):
        return await self._client._send_command('!ZMUTEON')

    async def off(self):
        return await self._client._send_command('!ZMUTEOFF')

    async def toggle(self):
        return await self._client._send_command('!ZMUTE')

    async def get(self) -> bool | None:
        response = await self._client._send_command('!ZMUTE?')
        if response and '!ZMUTE(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class AsyncZone2SourceControl(Zone2SourceControl):
    async def set(self, source: int):
        return await self._client._send_command(f'!ZSRC({source})')

    async def get(self) -> dict[str, Any | None]:
        response = await self._client._send_command('!ZSRC?')
        if response and '!ZSRC(' in response:
            parts = response.split('(')[1].split(')')
            source_num = int(parts[0])
            name = parts[1].strip().strip('"') if len(parts) > 1 else ''
            return {'source': source_num, 'name': name}
        return None

    async def next(self):
        return await self._client._send_command('!ZSRC+')

    async def previous(self):
        return await self._client._send_command('!ZSRC-')


class AsyncBassTrebleControl(BassTrebleControl):
    async def get_bass(self) -> int | None:
        response = await self._client._send_command('!TRIMBASS?')
        if response and '!TRIMBASS(' in response:
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None

    async def set_bass(self, level: int):
        return await self._client._send_command(f'!TRIMBASS({level})')

    async def bass_up(self):
        return await self._client._send_command('!TRIMBASS+')

    async def bass_down(self):
        return await self._client._send_command('!TRIMBASS-')

    async def get_treble(self) -> int | None:
        response = await self._client._send_command('!TRIMTREB?')
        if response and ('!TRIMTREB(' in response or '!TRIMTREBLE(' in response):
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None

    async def set_treble(self, level: int):
        level = max(-120, min(120, level))
        return await self._client._send_command(f'!TRIMTREB({level})')

    async def treble_up(self):
        return await self._client._send_command('!TRIMTREB+')

    async def treble_down(self):
        return await self._client._send_command('!TRIMTREB-')


class AsyncLoudnessControl(LoudnessControl):
    async def on(self):
        return await self._client._send_command('!LOUDNESS(1)')

    async def off(self):
        return await self._client._send_command('!LOUDNESS(0)')

    async def get(self) -> bool | None:
        response = await self._client._send_command('!LOUDNESS?')
        if response and '!LOUDNESS(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class AsyncLipsyncControl(LipsyncControl):
    async def get(self) -> int | None:
        response = await self._client._send_command('!LIPSYNC?')
        if response and '!LIPSYNC(' in response:
            value = response.split('(')[1].split(')')[0]
            return int(value)
        return None

    async def set(self, value: int):
        return await self._client._send_command(f'!LIPSYNC({value})')

    async def up(self):
        return await self._client._send_command('!LIPSYNC+')

    async def down(self):
        return await self._client._send_command('!LIPSYNC-')

    async def get_range(self) -> dict[str, int | None]:
        response = await self._client._send_command('!LIPSYNCRANGE?')
        if response and '!LIPSYNCRANGE(' in response:
            values = response.split('(')[1].split(')')[0].split(',')
            if len(values) == 2:
                return {'min': int(values[0]), 'max': int(values[1])}
        return None


class AsyncChannelTrimControl(ChannelTrimControl):
    async def get_center(self) -> int | None:
        response = await self._client._send_command('!TRIMCENTER?')
        if response and '!TRIMCENTER(' in response:
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None

    async def set_center(self, level: int):
        return await self._client._send_command(f'!TRIMCENTER({level})')

    async def center_up(self):
        return await self._client._send_command('!TRIMCENTER+')

    async def center_down(self):
        return await self._client._send_command('!TRIMCENTER-')

    async def get_lfe(self) -> int | None:
        response = await self._client._send_command('!TRIMLFE?')
        if response and '!TRIMLFE(' in response:
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None

    async def set_lfe(self, level: int):
        return await self._client._send_command(f'!TRIMLFE({level})')

    async def lfe_up(self):
        return await self._client._send_command('!TRIMLFE+')

    async def lfe_down(self):
        return await self._client._send_command('!TRIMLFE-')

    async def get_surrounds(self) -> int | None:
        response = await self._client._send_command('!TRIMSURRS?')
        if response and '!TRIMSURRS(' in response:
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None

    async def set_surrounds(self, level: int):
        return await self._client._send_command(f'!TRIMSURRS({level})')

    async def surrounds_up(self):
        return await self._client._send_command('!TRIMSURRS+')

    async def surrounds_down(self):
        return await self._client._send_command('!TRIMSURRS-')

    async def get_height(self) -> int | None:
        response = await self._client._send_command('!TRIMHEIGHT?')
        if response and '!TRIMHEIGHT(' in response:
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None

    async def set_height(self, level: int):
        return await self._client._send_command(f'!TRIMHEIGHT({level})')

    async def height_up(self):
        return await self._client._send_command('!TRIMHEIGHT+')

    async def height_down(self):
        return await self._client._send_command('!TRIMHEIGHT-')


class AsyncDeviceControl(DeviceControl):
    async def name(self) -> str | None:
        response = await self._client._send_command('!DEVICE?')
        if response and '!DEVICE(' in response:
            return response.split('(')[1].split(')')[0]
        return None

    async def ping(self) -> bool:
        response = await self._client._send_command('!PING?')
        return response == '!PONG'
