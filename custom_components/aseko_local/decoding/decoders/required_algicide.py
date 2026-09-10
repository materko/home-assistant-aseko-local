"""Algicide dose setpoint (ml/m3/day).

Independent ports (OXY, HOME): byte[72].  Confirmed on OXY (2026-04-11,
    value 15) and HOME (2026-04-28, serial 110128063, value 0).
Shared port (SALT, NET): byte[54], ours only while byte[37] bit 0x80 routes
    the port to algicide; see flowrate_algicide for the routing.
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


class RequiredAlgicide(Feature):
    """v7: byte[72], or byte[54] when byte[37] routes the shared port to algicide."""

    field = "required_algicide"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | None:
        """Independent algicide port."""
        return byte_or_none(frame[72])

    def decode_v7_routed_by_byte37(
        self, frame: V7Frame, device: AsekoDevice
    ) -> int | None:
        """Shared third-pump port, ours only while byte[37] bit 0x80 is set."""
        b = frame[37]
        if b == UNSPECIFIED_VALUE or not b & SHARED_PORT_IS_ALGICIDE:
            return None
        return byte_or_none(frame[54])
