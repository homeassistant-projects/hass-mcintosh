# McIntosh A/V Control for Home Assistant

![beta_badge](https://img.shields.io/badge/maturity-Beta-yellow.png)
![release_badge](https://img.shields.io/github/v/release/rsnodgrass/hass-mcintosh.svg)
![release_date](https://img.shields.io/github/release-date/rsnodgrass/hass-mcintosh.svg)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/MIT)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=WREP29UDAMB6G)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/DYks67r)
[![Support on Patreon][patreon-shield]][patreon]


![McIntosh Logo](https://raw.githubusercontent.com/rsnodgrass/hass-mcintosh/main/brands/logo.png)

Control your McIntosh MX160, MX170, or MX180 audio/video processor from Home Assistant via RS232 or IP connection.

## Status

**Ready for testing!** The integration is feature-complete and ready for hardware testing. If you have an MX160, MX170, or MX180, please test and report any issues.

## Features

- Full media player control (power, volume, mute, source selection)
- Support for all 26 source inputs (HDMI, SPDIF, USB, Analog, Balanced, Phono)
- Custom source naming via UI configuration
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

This integration is completely configured via config flow.

#### Example OLD-STYLE configuration.yaml:

```yaml
media_player:
  - platform: mcintosh
    model: mx160
    url: /dev/ttyUSB0
    sources:
      1:
        name: "Sonos"
      5:
        name: "FireTV"
```

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

| Feature | Main Zone | Zone 2 |
|---------|-----------|--------|
| Power On/Off | ✅ | ✅ (via library) |
| Volume Control | ✅ | ✅ (via library) |
| Mute | ✅ | ✅ (via library) |
| Source Selection | ✅ | ✅ (via library) |
| Volume Range | 0-99 | 0-99 |

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

- **Issues**: [GitHub Issues](https://github.com/rsnodgrass/hass-mcintosh/issues)
- **Community**: [Home Assistant Community Forum](https://community.home-assistant.io/t/mcintosh-dayton-audio-sonance-multi-zone-amps/450908)
- **Pull Requests**: Contributions welcome!

## Technical Details

This integration uses the embedded `pymcintosh` Python library for communication with McIntosh processors. The library implements the McIntosh RS232/IP protocol with:

- Async/await support for Home Assistant
- Command throttling to prevent device overload
- Proper error handling and recovery
- Model-specific configurations (MX160/MX170/MX180)

## See Also

* [pymcintosh library](pymcintosh/) - Standalone Python library for McIntosh control
* [RS232 Protocol Documentation](pymcintosh/models.py) - Command reference
* [Example Usage](pymcintosh/example-async.py) - Python library examples




[forum]: https://forum/mcintosh
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg
[patreon]: https://www.patreon.com/rsnodgrass
[patreon-shield]: https://frenck.dev/wp-content/uploads/2019/12/patreon.png
[project-stage-shield]: https://img.shields.io/badge/project%20stage-production%20ready-brightgreen.svg
