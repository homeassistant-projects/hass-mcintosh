"""Various utilities for the McIntosh integration."""

from __future__ import annotations

from typing import Any

from .const import CONF_BAUD_RATE


def get_connection_overrides(config: dict[str, Any]) -> dict[str, Any]:
    """Get serial config overrides for pymcintosh from HA config."""
    config_overrides: dict[str, Any] = {}
    if baud := config.get(CONF_BAUD_RATE):
        config_overrides['baudrate'] = baud
    return config_overrides
