"""Flocculant dose setpoint (ml/h).

Independent ports (OXY, HOME): byte[54].  Confirmed on OXY (2026-04-11,
    value 10) and HOME (2026-04-28, serial 110128063, value 10).
Shared port (SALT, NET): byte[54] as well, but ours only while byte[37] bit
    0x80 is clear; see flowrate_floc for the routing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...const import UNSPECIFIED_VALUE
from ..feature import Feature
from ..frame import byte_or_none

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


SHARED_PORT_IS_ALGICIDE = 0x80


class RequiredFloc(Feature):
    """v7: byte[54], on a shared port only while byte[37] routes it to flocculant."""

    field = "required_floc"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | None:
        """Independent flocculant port."""
        return byte_or_none(frame[54])

    def decode_v7_routed_by_byte37(
        self, frame: V7Frame, device: AsekoDevice
    ) -> int | None:
        """Shared third-pump port, ours only while byte[37] bit 0x80 is clear."""
        b = frame[37]
        if b == UNSPECIFIED_VALUE or b & SHARED_PORT_IS_ALGICIDE:
            return None
        return byte_or_none(frame[54])
