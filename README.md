# McIntosh A/V Control for Home Assistant

![release_badge](https://img.shields.io/github/v/release/homeassistant-community/hass-mcintosh.svg)
![release_date](https://img.shields.io/github/release-date/homeassistant-community/hass-mcintosh.svg)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/MIT)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=WREP29UDAMB6G)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/DYks67r)
[![Support on Patreon][patreon-shield]][patreon]


![McIntosh Logo](https://github.com/homeassistant-projects/hass-mcintosh/blob/main/brands/logo.png?raw=true)

Control your McIntosh MX160, MX170, or MX180 audio/video processor from Home Assistant via RS232 or IP connection.

## Status

**Implementation Complete!** This integration is fully implemented with config flow UI, source customization, and all basic media player controls. Ready for hardware testing with McIntosh MX160, MX170, or MX180 processors.

## Features

- Full media player control (power, volume, mute, source selection)
- Support for all 26 source inputs (HDMI, SPDIF, USB, Analog, Balanced, Phono)
- Custom source naming via UI configuration
- Advanced audio controls:
  - Bass and treble trim (-12dB to +12dB)
  - Loudness on/off switch
  - Lipsync delay adjustment
  - Channel trim controls (center, LFE, surrounds, height)
- Zone 2 support (via pymcintosh library)
- RS232 serial and IP/socket connection support
- Config flow UI for easy setup
- Options flow for reconfiguration

## Supported Devices

| Model | Status | Notes |
|-------|--------|-------|
| McIntosh MX160 | Untested | Should work, needs hardware testing |
| McIntosh MX170 | Untested | Should work, needs hardware testing |
| McIntosh MX180 | Untested | Should work, needs hardware testing |

**Note:** All models use the same RS232/IP protocol. If you can test with hardware, please report your results!

## Installation

### Step 1: Install Custom Components

ake sure that [Home Assistant Community Store (HACS)](https://github.com/custom-components/hacs) is installed and then add the "Integration" repository: `rsnodgrass/hass-mcintosh`.

### Step 2: Configuration

This integration uses **Config Flow** for setup - no YAML configuration needed!

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **McIntosh**
4. Follow the setup wizard to configure your processor

You can customize source names through the **Options** menu after setup.

## Hardware Requirements

### RS232 Connection

- **RS232 to USB adapter**: [Example cable](https://www.amazon.com/RS232-to-USB/dp/B0759HSLP1?tag=carreramfi-20)
- **Baud rate**: 115200 (default)
- **Protocol**: 8N1 (8 data bits, no parity, 1 stop bit)

### IP/Network Connection

- **Port**: 84 (default)
- Your McIntosh processor must support network control
- Ensure your processor is connected to your network

## Supported Controls

| Feature | Main Zone | Zone 2 | Entity Type |
|---------|-----------|--------|-------------|
| Power On/Off | ✅ | ✅ (via library) | media_player |
| Volume Control | ✅ | ✅ (via library) | media_player |
| Mute | ✅ | ✅ (via library) | media_player |
| Source Selection | ✅ | ✅ (via library) | media_player |
| Bass Trim | ✅ | N/A | number |
| Treble Trim | ✅ | N/A | number |
| Loudness | ✅ | N/A | switch |
| Lipsync Delay | ✅ | N/A | number |
| Center Channel Trim | ✅ | N/A | number |
| LFE Channel Trim | ✅ | N/A | number |
| Surround Channels Trim | ✅ | N/A | number |
| Height Channels Trim | ✅ | N/A | number |
| Volume Range | 0-99 | 0-99 | - |

**Note:** Zone 2 controls are available through the pymcintosh library but not yet exposed in the HA UI.

## Source Inputs

All 26 McIntosh source inputs are supported:

- **HDMI 1-8** (sources 0-7)
- **Audio Return** (source 8)
- **SPDIF 1-8** (sources 9-16): Optical and Coaxial digital
- **USB Audio** (source 17)
- **Analog 1-4** (sources 18-21)
- **Balanced 1-2** (sources 22-23)
- **Phono** (source 24)
- **8 Channel Analog** (source 25)

## Troubleshooting

### Connection Issues

- Verify the correct serial port or IP address
- Check that your RS232 cable is properly connected
- Ensure baud rate matches your processor settings (default: 115200)
- For IP connections, verify port 84 is accessible

### Integration Not Loading

- Check Home Assistant logs for error messages
- Verify `pymcintosh` directory exists in HA root
- Restart Home Assistant after installation

## Support

- **Issues**: [GitHub Issues](https://github.com/homeassistant-community/hass-mcintosh/issues)
- **Community**: [Home Assistant Community Forum](https://community.home-assistant.io/t/mcintosh-dayton-audio-sonance-multi-zone-amps/450908)
- **Pull Requests**: Contributions welcome!

## Technical Details

This integration uses an embedded Python library (`pymcintosh`) for communication with McIntosh processors. The library implements the McIntosh RS232/IP protocol with:

- Async/await support for Home Assistant
- Command throttling to prevent device overload
- Proper error handling and recovery
- Model-specific configurations (MX160/MX170/MX180)

The library is embedded within `custom_components/mcintosh/pymcintosh/` and is automatically installed with the integration.




[forum]: https://forum/mcintosh
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg
[patreon]: https://www.patreon.com/rsnodgrass
[patreon-shield]: https://frenck.dev/wp-content/uploads/2019/12/patreon.png
[project-stage-shield]: https://img.shields.io/badge/project%20stage-production%20ready-brightgreen.svg
