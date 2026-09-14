"""v8: the text frame, firmware 8.x.

A ``V8Frame`` wraps the frame's parsed sections; features read individual
values off it and never touch the transport again.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ...const import UNSPECIFIED_V8
from .protocol import Protocol

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
