"""Algicide dose setpoint (ml/m3/day).

Independent ports (OXY, HOME): byte[72].  Confirmed on OXY (2026-04-11,
    value 15) and HOME (2026-04-28, serial 110128063, value 0).
Shared port (SALT, NET): byte[54], ours only while byte[37] bit 0x80 routes
    the port to algicide; see algaecide_flow_rate for the routing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...const import UNSPECIFIED_VALUE
from ..feature import Feature
from ..frames import byte_or_absent
from ..presence import NOT_PRESENT

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frames import V7Frame
    from ..presence import NotPresent


SHARED_PORT_IS_ALGICIDE = 0x80


class AlgaecideDoseTarget(Feature):
    """v7: byte[72], or byte[54] when byte[37] routes the shared port to algicide."""

    field = "algaecide_dose_target"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | NotPresent:
        """Independent algicide port."""
        return byte_or_absent(frame[72])

    def decode_v7_routed_by_byte37(
        self, frame: V7Frame, device: AsekoDevice
    ) -> int | NotPresent:
        """Shared third-pump port, ours only while byte[37] bit 0x80 is set."""
        b = frame[37]
        if b == UNSPECIFIED_VALUE or not b & SHARED_PORT_IS_ALGICIDE:
            return NOT_PRESENT
        return byte_or_absent(frame[54])
