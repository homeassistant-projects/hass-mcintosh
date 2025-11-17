# pymcintosh - Python Library for McIntosh Processors

Python library for controlling McIntosh MX160, MX170, and MX180 A/V processors via RS232 serial or IP connection.

## Supported Models

| Model | Status | Notes |
|-------|--------|-------|
| MX160 | Tested | Base model support |
| MX170 | Untested | Adds max volume query |
| MX180 | Untested | Based on MX170 protocol |

## Installation

```bash
pip install pymcintosh
```

Or install from source:

```bash
cd pymcintosh
pip install -e .
```

## Quick Start

### Synchronous API

```python
from pymcintosh import get_mcintosh

# connect via serial port
client = get_mcintosh('mx160', '/dev/ttyUSB0')

# or connect via network
client = get_mcintosh('mx160', 'socket://192.168.1.100:84')

# control the device
client.power.on()
client.volume.set(50)
client.source.set(0)  # HDMI 1

# query status
volume = client.volume.get()
power = client.power.get()
source_info = client.source.get()

print(f'Power: {power}, Volume: {volume}, Source: {source_info}')

# Zone 2 control
client.zone_2.power.on()
client.zone_2.volume.set(30)
client.zone_2.source.set(1)  # HDMI 2
```

### Asynchronous API

```python
import asyncio
from pymcintosh import async_get_mcintosh

async def main():
    loop = asyncio.get_event_loop()

    # connect to device
    client = await async_get_mcintosh('mx160', '/dev/ttyUSB0', loop)

    # control device
    await client.power.on()
    await client.volume.set(50)

    # query status
    volume = await client.volume.get()
    power = await client.power.get()

    print(f'Power: {power}, Volume: {volume}')

asyncio.run(main())
```

## Connection URLs

This library uses pyserial URL format for connections:

| URL Format | Example | Description |
|------------|---------|-------------|
| `/dev/ttyUSB0` | `/dev/ttyUSB0` | Direct serial (Linux) |
| `COM3` | `COM3` | Direct serial (Windows) |
| `socket://host:port` | `socket://192.168.1.100:84` | Network connection (IP port 84) |
| `socket://hostname:port` | `socket://mx160.local:84` | Network via hostname |

## API Reference

### Power Control

```python
client.power.on()           # turn system on
client.power.off()          # turn system off
client.power.toggle()       # toggle power state
status = client.power.get() # get power status (True/False)
```

### Volume Control

```python
client.volume.set(50)       # set volume (0-99)
client.volume.up()          # increase volume
client.volume.up(5)         # increase by 5
client.volume.down()        # decrease volume
client.volume.down(3)       # decrease by 3
level = client.volume.get() # get current volume

# MX170/MX180 only
max_vol = client.volume.max_vol()  # get max volume setting
```

### Mute Control

```python
client.mute.on()            # mute on
client.mute.off()           # mute off
client.mute.toggle()        # toggle mute
status = client.mute.get()  # get mute status (True/False)
```

### Source Control

```python
client.source.set(0)        # set source (0=HDMI 1, 1=HDMI 2, etc)
client.source.next()        # next source
client.source.previous()    # previous source
info = client.source.get()  # get current source info

# get info for specific source
info = client.source.info(5)  # info for source 5 (HDMI 6)
```

### Zone 2 Control

All main zone controls are available for Zone 2:

```python
client.zone_2.power.on()
client.zone_2.power.off()
client.zone_2.volume.set(30)
client.zone_2.volume.up()
client.zone_2.mute.toggle()
client.zone_2.source.set(1)
```

### Device Info

```python
name = client.device.name()  # get device name (e.g. 'MX160')
pong = client.device.ping()  # ping test (returns True if alive)
```

## Source Inputs

| Number | Input Name |
|--------|-----------|
| 0 | HDMI 1 |
| 1 | HDMI 2 |
| 2 | HDMI 3 |
| 3 | HDMI 4 |
| 4 | HDMI 5 |
| 5 | HDMI 6 |
| 6 | HDMI 7 |
| 7 | HDMI 8 |
| 8 | Audio Return |
| 9 | SPDIF 1 (Optical) |
| 10 | SPDIF 2 (Optical) |
| 11 | SPDIF 3 (Optical) |
| 12 | SPDIF 4 (Optical) |
| 13 | SPDIF 5 (AES/EBU) |
| 14 | SPDIF 6 (Coaxial) |
| 15 | SPDIF 7 (Coaxial) |
| 16 | SPDIF 8 (Coaxial) |
| 17 | USB Audio |
| 18 | Analog 1 |
| 19 | Analog 2 |
| 20 | Analog 3 |
| 21 | Analog 4 |
| 22 | Balanced 1 |
| 23 | Balanced 2 |
| 24 | Phono |
| 25 | 8 Channel Analog |

## Configuration Overrides

### Custom Baud Rate

```python
# use 9600 baud instead of default 115200
client = get_mcintosh('mx160', '/dev/ttyUSB0', baudrate=9600)
```

### Custom Timeout

```python
# increase timeout to 5 seconds
client = get_mcintosh('mx160', '/dev/ttyUSB0', timeout=5.0)
```

## Model Differences

### MX160
- Base model with full RS232 protocol
- Default baud: 115200
- Min time between commands: 0.4 seconds

### MX170
- Adds `client.volume.max_vol()` to query maximum volume setting
- Different treble trim response format
- Min time between commands: 0.4 seconds

### MX180
- Inherits MX170 features
- Removes some HDMI output and multiview commands
- Min time between commands: 0.1 seconds (faster)

## Technical Details

- **Protocol**: RS232 with `\r` (carriage return) line endings
- **Default Baud**: 115200 (9600 also supported)
- **Network Port**: TCP port 84
- **Rate Limiting**: Commands are automatically throttled per model specs
- **Thread Safety**: Synchronous client uses threading locks
- **Async Support**: Full asyncio support via serial_asyncio

## Related Projects

- [hass-mcintosh](https://github.com/homeassistant-community/hass-mcintosh) - Home Assistant integration
- [pyavcontrol](https://github.com/homeassistant-community/pyavcontrol) - Generalized A/V control library
- [pyxantech](https://github.com/homeassistant-community/pyxantech) - Similar library for Xantech amps

## License

Apache 2.0
