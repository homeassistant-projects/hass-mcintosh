"""Constants for the McIntosh integration."""

from __future__ import annotations

from typing import Final

from .pymcintosh.models import DEFAULT_IP_PORT, SUPPORTED_MODELS

DOMAIN: Final = 'mcintosh'

DEFAULT_URL: Final = f'socket://mcintosh.local:{DEFAULT_IP_PORT}'
DEFAULT_SCAN_INTERVAL: Final = 30

COMPATIBLE_MODELS: list[str] = SUPPORTED_MODELS

# connection configuration
CONF_URL: Final = 'url'
CONF_BAUD_RATE: Final = 'baudrate'
CONF_MODEL: Final = 'model_id'

# zone configuration
CONF_MAIN_ZONE_NAME: Final = 'main_zone_name'
CONF_ZONE_2_ENABLED: Final = 'zone_2_enabled'
CONF_ZONE_2_NAME: Final = 'zone_2_name'
CONF_ZONE_3_ENABLED: Final = 'zone_3_enabled'
CONF_ZONE_3_NAME: Final = 'zone_3_name'

# source configuration
CONF_SOURCES: Final = 'sources'
CONF_ENABLED_SOURCE_GROUPS: Final = 'enabled_source_groups'

# feature toggles
CONF_ENABLE_LOUDNESS: Final = 'enable_loudness'
CONF_ENABLE_AUDIO_TRIM: Final = 'enable_audio_trim'
CONF_ENABLE_CHANNEL_TRIM: Final = 'enable_channel_trim'
CONF_ENABLE_LIPSYNC: Final = 'enable_lipsync'
CONF_POLLING_INTERVAL: Final = 'polling_interval'

# default values
DEFAULT_MAIN_ZONE_NAME: Final = 'Main Zone'
DEFAULT_ZONE_2_NAME: Final = 'Zone 2'
DEFAULT_ZONE_3_NAME: Final = 'Zone 3'
