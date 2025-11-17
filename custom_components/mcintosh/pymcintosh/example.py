#!/usr/bin/env python3
"""Example synchronous usage of pymcintosh library."""

import argparse
import logging

from pymcintosh import get_mcintosh, SUPPORTED_MODELS

# setup logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


def main():
    parser = argparse.ArgumentParser(description='McIntosh RS232 client example')
    parser.add_argument(
        '--port',
        required=True,
        help='Serial port or socket URL (e.g. /dev/ttyUSB0 or socket://192.168.1.100:84)',
    )
    parser.add_argument(
        '--model',
        default='mx160',
        choices=SUPPORTED_MODELS,
        help=f'McIntosh model ({", ".join(SUPPORTED_MODELS)})',
    )
    parser.add_argument(
        '--baud',
        type=int,
        default=115200,
        help='Baud rate (default: 115200)',
    )
    args = parser.parse_args()

    print(f'Connecting to {args.model} at {args.port} (baud: {args.baud})...')

    # create client
    client = get_mcintosh(args.model, args.port, baudrate=args.baud)

    # get device info
    device_name = client.device.name()
    print(f'\nConnected to: {device_name}')

    # test ping
    if client.device.ping():
        print('Device responds to ping')

    # get current status
    print('\n=== Current Status ===')
    power = client.power.get()
    volume = client.volume.get()
    mute = client.mute.get()
    source = client.source.get()

    print(f'Power: {power}')
    print(f'Volume: {volume}')
    print(f'Mute: {mute}')
    print(f'Source: {source}')

    # demonstrate controls
    print('\n=== Testing Controls ===')

    # power on
    print('Turning power on...')
    client.power.on()

    # set volume
    print('Setting volume to 50...')
    client.volume.set(50)

    # unmute
    print('Unmuting...')
    client.mute.off()

    # set source to HDMI 1
    print('Setting source to HDMI 1...')
    client.source.set(0)

    # demonstrate volume up/down
    print('Volume up...')
    client.volume.up()
    print('Volume down...')
    client.volume.down()

    # test Zone 2
    print('\n=== Testing Zone 2 ===')
    print('Turning Zone 2 on...')
    client.zone_2.power.on()

    print('Setting Zone 2 volume to 30...')
    client.zone_2.volume.set(30)

    print('Setting Zone 2 source to HDMI 2...')
    client.zone_2.source.set(1)

    zone2_volume = client.zone_2.volume.get()
    zone2_source = client.zone_2.source.get()
    print(f'Zone 2 Volume: {zone2_volume}')
    print(f'Zone 2 Source: {zone2_source}')

    # MX170/MX180 specific features
    if args.model in ['mx170', 'mx180']:
        print('\n=== MX170/MX180 Features ===')
        max_vol = client.volume.max_vol()
        print(f'Maximum volume setting: {max_vol}')

    print('\nExample complete!')


if __name__ == '__main__':
    main()
