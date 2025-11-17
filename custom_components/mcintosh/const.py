"""Constants for the McIntosh integration"""

from __future__ import annotations

from typing import Final

# import from local pymcintosh package
import sys
from pathlib import Path

# add pymcintosh to path if not already there
pymcintosh_path = Path(__file__).parent.parent.parent / 'pymcintosh'
if str(pymcintosh_path) not in sys.path:
    sys.path.insert(0, str(pymcintosh_path))

from pymcintosh.models import SUPPORTED_MODELS, DEFAULT_IP_PORT

DOMAIN: Final[str] = 'mcintosh'

DEFAULT_URL: Final = f'socket://mcintosh.local:{DEFAULT_IP_PORT}'

CONF_URL: Final = 'url'
CONF_BAUD_RATE: Final = 'baudrate'
CONF_MODEL: Final = 'model_id'
CONF_SOURCES: Final = 'sources'

COMPATIBLE_MODELS: list[str] = SUPPORTED_MODELS
