"""Constants for the McIntosh integration."""

from __future__ import annotations

from typing import Final

from .pymcintosh.models import DEFAULT_IP_PORT, SUPPORTED_MODELS

DOMAIN: Final = 'mcintosh'

DEFAULT_URL: Final = f'socket://mcintosh.local:{DEFAULT_IP_PORT}'

CONF_URL: Final = 'url'
CONF_BAUD_RATE: Final = 'baudrate'
CONF_MODEL: Final = 'model_id'
CONF_SOURCES: Final = 'sources'

COMPATIBLE_MODELS: list[str] = SUPPORTED_MODELS
