"""Frame parsers: raw bytes to a protocol-specific view.

This is the only place that knows how a frame is laid out as a whole.  A
``V7Frame`` wraps the 120-byte binary frame; a ``V8Frame`` wraps the text
frame's parsed sections.  Feature decoders read individual values off these
views and never touch the raw transport again.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import TypeVar

import homeassistant.util

from ..const import UNSPECIFIED_V8, UNSPECIFIED_VALUE, YEAR_OFFSET
from .presence import NOT_PRESENT, NotPresent

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


class Protocol(Enum):
    """The two wire formats an Aseko unit can speak."""

    V7 = "v7"  # 120-byte binary frame, firmware <= 7.x, port 47524
    V8 = "v8"  # text frame starting with "{v1 ", firmware 8.x, port 51050


# Signature that opens every v8 text frame.
V8_SIGNATURE = b"{v1 "


# ---------------------------------------------------------------------------
# v7: 120-byte binary frame
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class V7Frame:
    """Read-only view over a 120-byte binary frame.

    ``frame[i]`` and ``frame[a:b]`` index the raw bytes; ``frame.word(i)``
    reads the big-endian 16-bit value at ``i``.
    """

    raw: bytes
    protocol: Protocol = field(default=Protocol.V7, init=False)

    def __getitem__(self, index: int | slice) -> int | bytes:
        return self.raw[index]

    def word(self, index: int) -> int:
        """Return the unsigned big-endian 16-bit value at ``index``."""
        return int.from_bytes(self.raw[index : index + 2], "big")

    @property
    def serial_number(self) -> int:
        """Serial number, bytes 0-3."""
        return int.from_bytes(self.raw[0:4], "big")

    @property
    def unit_type(self) -> int:
        """The device-type / probe-configuration byte, byte[4]."""
        return self.raw[4]


V7_SEGMENT_LENGTH = 40
V7_CHECKSUM_SEED = 0xAA

# Serials whose bad checksum was already logged as a warning; later ones go to
# debug so a unit that keeps sending them does not flood the log.
_checksum_warned: set[int] = set()


def v7_bad_checksum_segments(raw: bytes) -> list[int]:
    """Return the indexes (0-2) of the 40-byte segments whose checksum fails.

    The last byte of every segment (39, 79, 119) is 0xAA XOR the 39 bytes
    before it -- the rule of the manufacturer's RS485 protocol document,
    which matches every segment of the captured v7 frames.  A trailing
    partial segment is not checked.
    """
    bad = []
    for index in range(len(raw) // V7_SEGMENT_LENGTH):
        start = index * V7_SEGMENT_LENGTH
        checksum = V7_CHECKSUM_SEED
        for value in raw[start : start + V7_SEGMENT_LENGTH - 1]:
            checksum ^= value
        if checksum != raw[start + V7_SEGMENT_LENGTH - 1]:
            bad.append(index)
    return bad


def parse_v7(raw: bytes) -> V7Frame:
    """Wrap a binary frame.  Alignment is the server's job, not this one's.

    A failed segment checksum is only logged: the frame is decoded as before.
    """
    frame = V7Frame(bytes(raw))
    bad = v7_bad_checksum_segments(frame.raw)
    if bad:
        serial = frame.serial_number if len(frame.raw) >= 4 else 0
        log = _LOGGER.debug if serial in _checksum_warned else _LOGGER.warning
        _checksum_warned.add(serial)
        log(
            "v7 frame from serial %s failed the checksum of segment(s) %s; "
            "decoding it anyway. Frame: %s",
            serial,
            bad,
            frame.raw.hex(),
        )
    return frame


def normalize_value(value: int | str | None, type_: type[T]) -> T | None:
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


def decode_timestamp(data: bytes) -> datetime:
    """Decode the device clock from bytes 6-11, falling back to now()."""
    if (
        len(data) < 12
        or data[6] == UNSPECIFIED_VALUE
        or data[7] == UNSPECIFIED_VALUE
        or data[8] == UNSPECIFIED_VALUE
        or data[9] == UNSPECIFIED_VALUE
        or data[10] == UNSPECIFIED_VALUE
        or data[11] == UNSPECIFIED_VALUE
    ):
        _LOGGER.info(
            "Received unspecified timestamp - falling back to now(). Frame: %s",
            data.hex(),
        )
        return datetime.now(tz=homeassistant.util.dt.get_default_time_zone())

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
    except ValueError as e:
        _LOGGER.warning(
            "Received invalid timestamp (%s) - falling back to now(). Frame: %s",
            e,
            data.hex(),
        )
        return datetime.now(tz=homeassistant.util.dt.get_default_time_zone())


# ---------------------------------------------------------------------------
# v8: text frame
# ---------------------------------------------------------------------------

# Matches "sectionname: <values>" up to the next section keyword or the end.
_SECTION_RE = re.compile(r"(\w+):\s*(.*?)(?=\s+\w+:|$)", re.DOTALL)
_HEADER_RE = re.compile(r"v1\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)")


@dataclass(frozen=True)
class V8Frame:
    """Read-only view over a parsed v8 text frame.

    Frame format::

        {v1 <serial> <f2> <f3> <f4>
         ins: <i0> <i1> ... <iN>
         ains: <a0> <a1> ... <aN>
         outs: <o0> <o1> ... <oN>
         areqs: <r0> <r1> ... <rN>
         reqs: ...
         fncs: ...
         mods: ...
         flags: ...
         crc16: XXXX}

    ``get(section, i)`` returns the integer at ``i`` or None when the section
    is shorter; ``value(section, i)`` additionally maps the ``-500`` sentinel
    (absent / unreadable probe) to None.
    """

    raw: bytes
    serial_number: int
    header_type: int
    sections: dict[str, list[int]]
    protocol: Protocol = field(default=Protocol.V8, init=False)

    def get(self, section: str, index: int) -> int | None:
        """Return ``sections[section][index]``, or None if out of range."""
        values = self.sections.get(section, [])
        return values[index] if index < len(values) else None

    def value(self, section: str, index: int) -> int | None:
        """Like ``get`` but also None for the v8 sentinel (-500)."""
        v = self.get(section, index)
        return None if v is None or v == UNSPECIFIED_V8 else v


def parse_v8(raw: bytes) -> V8Frame:
    """Parse a v8 text frame.  Raises ValueError if it cannot be parsed."""
    try:
        text = raw.decode("ascii", errors="replace").strip()
    except Exception as exc:
        raise ValueError(f"v8 frame is not ASCII: {exc}") from exc

    if not text.startswith("{") or not text.endswith("}"):
        raise ValueError(f"v8 frame missing braces: {text[:40]!r}")
    body = text[1:-1].strip()

    header_match = _HEADER_RE.match(body)
    if not header_match:
        raise ValueError(f"v8 frame header not recognised: {body[:60]!r}")
    serial_number = int(header_match.group(1))
    header_type = int(header_match.group(2))

    sections: dict[str, list[int]] = {}
    for m in _SECTION_RE.finditer(body):
        name = m.group(1)
        if name == "v1":
            continue  # header - already parsed
        try:
            sections[name] = [int(v) for v in m.group(2).split()]
        except ValueError:
            # crc16 is hex, not decimal - keep the section, ignore the value
            sections[name] = []

    return V8Frame(
        raw=bytes(raw),
        serial_number=serial_number,
        header_type=header_type,
        sections=sections,
    )


def parse_frame(raw: bytes) -> V7Frame | V8Frame:
    """Detect the protocol from the first bytes and parse accordingly."""
    if bytes(raw).lstrip(b"\r\n\t\x00").startswith(V8_SIGNATURE):
        return parse_v8(raw)
    return parse_v7(raw)
