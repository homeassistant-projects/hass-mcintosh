"""Various utilities for the McIntosh integration"""

from .const import CONF_BAUD_RATE


def get_connection_overrides(config: dict) -> dict:
    """Get serial config overrides for pymcintosh from HA config."""
    config_overrides = {}
    if baud := config.get(CONF_BAUD_RATE):
        config_overrides['baudrate'] = baud
    return config_overrides
