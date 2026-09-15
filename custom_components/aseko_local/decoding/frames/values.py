"""Reading single values out of a frame: unset markers, times, the clock.

Shared by both protocols' features.  0xFF (a byte) and 0xFFFF (a word) are
the markers of a value the unit did not fill in.
"""

from __future__ import annotations

import logging
from datetime import datetime, time

import homeassistant.util

from ...const import UNSPECIFIED_VALUE, YEAR_OFFSET
from ..presence import NOT_PRESENT, NotPresent

_LOGGER = logging.getLogger(__name__)

# Two 0xFF bytes: a 16-bit value the unit did not fill in.
UNSPECIFIED_WORD = 0xFFFF


def normalize_value[T](value: int | str | None, type_: type[T]) -> T | None:
    """Normalize a raw value to None if it is unspecified or invalid.

    Rules:
    - None stays None
    - Integer 255 (0xFF) -> None
    - Empty string "" -> None
    - String "255" -> None
    - Otherwise: return value unchanged
    """
    if value is None:
        return None

    if type_ is int and isinstance(value, int):
        return None if value == UNSPECIFIED_VALUE else type_(value)

    if type_ is str and isinstance(value, str):
        val = value.strip()
        if not val or val == str(UNSPECIFIED_VALUE):
            return None
        return type_(val)

    raise ValueError(f"Unsupported type {type_} or value {value}")


def word_or_absent(value: int | None) -> int | NotPresent:
    """NOT_PRESENT for a 16-bit setting read as None by ``word_or_none``."""
    return NOT_PRESENT if value is None else value


def byte_or_absent(value: int) -> int | NotPresent:
    """Return ``value``, or NOT_PRESENT for the 0xFF "unspecified" marker.

    For a configuration byte 0xFF means the setting was never made or the
    input is not fitted, which is a fact about this unit rather than a value
    that happens to be unknown -- see ``presence``.
    """
    return NOT_PRESENT if value == UNSPECIFIED_VALUE else value


def decode_time(data: bytes) -> time | None:
    """Decode an (hour, minute) byte pair; 0xFF in the hour means unset."""
    if data[0] == UNSPECIFIED_VALUE:
        return None

    hour = data[0]
    minute = data[1]

    try:
        return time(hour=hour, minute=minute)
    except ValueError as e:
        _LOGGER.warning("Invalid time in frame (%s) - data=%s", e, data.hex())
        return None


def time_or_absent(data: bytes) -> time | NotPresent:
    """Like ``decode_time`` but NOT_PRESENT for an unset or invalid pair."""
    value = decode_time(data)
    return NOT_PRESENT if value is None else value


def unit_clock_v7(data: bytes) -> datetime | None:
    """The unit's clock from bytes 6-11 as sent, or None when unset or not a date.

    Wall-clock time in Home Assistant's time zone: the unit sends no zone.
    """
    if len(data) < 12 or UNSPECIFIED_VALUE in data[6:12]:
        return None
    try:
        return datetime(
            year=YEAR_OFFSET + data[6],
            month=data[7],
            day=data[8],
            hour=data[9],
            minute=data[10],
            second=data[11],
            tzinfo=homeassistant.util.dt.get_default_time_zone(),
        )
    except ValueError:
        return None


def unit_clock_v8(hour: int | None, minute: int | None) -> time | None:
    """A v8 unit's clock (hour and minute, no date), or None when not valid."""
    if hour is None or minute is None:
        return None
    try:
        return time(hour, minute)
    except (TypeError, ValueError):
        return None


def decode_timestamp(data: bytes) -> datetime:
    """Decode the device clock from bytes 6-11, falling back to now()."""
    clock = unit_clock_v7(data)
    if clock is not None:
        return clock
    if len(data) >= 12 and UNSPECIFIED_VALUE not in data[6:12]:
        # filled in, but not a date: worth a look, unlike the routine unset
        # bytes of a unit that sends no clock (v7 NET)
        _LOGGER.warning(
            "Received invalid timestamp %s - falling back to now()", data[6:12].hex()
        )
    return datetime.now(tz=homeassistant.util.dt.get_default_time_zone())
