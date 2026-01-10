"""McIntosh device model definitions and configurations."""

from __future__ import annotations

from typing import Any

# connection parameters
DEFAULT_BAUD_RATE = 115200
DEFAULT_TIMEOUT = 2.0
DEFAULT_IP_PORT = 84
RESPONSE_EOL = '\r'
COMMAND_EOL = '\r'

# rate limiting differs by model
MX160_MIN_TIME_BETWEEN_COMMANDS = 0.4  # seconds
MX170_MIN_TIME_BETWEEN_COMMANDS = 0.4  # seconds
MX180_MIN_TIME_BETWEEN_COMMANDS = 0.1  # seconds (may be faster)

# source input definitions (same across all models)
SOURCES: dict[int, str] = {
    0: 'HDMI 1',
    1: 'HDMI 2',
    2: 'HDMI 3',
    3: 'HDMI 4',
    4: 'HDMI 5',
    5: 'HDMI 6',
    6: 'HDMI 7',
    7: 'HDMI 8',
    8: 'Audio Return',
    9: 'SPDIF 1 (Optical)',
    10: 'SPDIF 2 (Optical)',
    11: 'SPDIF 3 (Optical)',
    12: 'SPDIF 4 (Optical)',
    13: 'SPDIF 5 (AES/EBU)',
    14: 'SPDIF 6 (Coaxial)',
    15: 'SPDIF 7 (Coaxial)',
    16: 'SPDIF 8 (Coaxial)',
    17: 'USB Audio',
    18: 'Analog 1',
    19: 'Analog 2',
    20: 'Analog 3',
    21: 'Analog 4',
    22: 'Balanced 1',
    23: 'Balanced 2',
    24: 'Phono',
    25: '8 Channel Analog',
}

MODEL_CONFIGS: dict[str, dict[str, Any]] = {
    'mx160': {
        'name': 'MX160',
        'description': 'McIntosh MX160 Processor',
        'tested': True,
        'min_time_between_commands': MX160_MIN_TIME_BETWEEN_COMMANDS,
        'supports_max_volume_query': False,
        'connection_init': '!VERB(2)',  # set to normal verbosity on connect
        'rs232': {
            'baudrate': DEFAULT_BAUD_RATE,
            'bytesize': 8,
            'parity': 'N',
            'stopbits': 1,
            'timeout': DEFAULT_TIMEOUT,
        },
        'ip': {
            'port': DEFAULT_IP_PORT,
        },
    },
    'mx170': {
        'name': 'MX170',
        'description': 'McIntosh MX170 Processor',
        'tested': False,
        'min_time_between_commands': MX170_MIN_TIME_BETWEEN_COMMANDS,
        'supports_max_volume_query': True,
        'connection_init': '!VERB(2)',
        'rs232': {
            'baudrate': DEFAULT_BAUD_RATE,
            'bytesize': 8,
            'parity': 'N',
            'stopbits': 1,
            'timeout': DEFAULT_TIMEOUT,
        },
        'ip': {
            'port': DEFAULT_IP_PORT,
        },
    },
    'mx180': {
        'name': 'MX180',
        'description': 'McIntosh MX180 Processor',
        'tested': False,
        'min_time_between_commands': MX180_MIN_TIME_BETWEEN_COMMANDS,
        'supports_max_volume_query': True,
        'connection_init': '!VERB(2)',
        'rs232': {
            'baudrate': DEFAULT_BAUD_RATE,
            'bytesize': 8,
            'parity': 'N',
            'stopbits': 1,
            'timeout': DEFAULT_TIMEOUT,
        },
        'ip': {
            'port': DEFAULT_IP_PORT,
        },
    },
}

SUPPORTED_MODELS = list(MODEL_CONFIGS.keys())


def get_model_config(model_id: str) -> dict[str, Any]:
    """Get configuration for a specific model."""
    if model_id not in MODEL_CONFIGS:
        raise ValueError(
            f"Unsupported model '{model_id}'. Supported: {SUPPORTED_MODELS}"
        )
    return MODEL_CONFIGS[model_id]
