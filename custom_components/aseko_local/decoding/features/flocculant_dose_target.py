"""Flocculant dose setpoint (ml/h).

Independent ports (OXY, HOME): byte[54].  Confirmed on OXY (2026-04-11,
    value 10) and HOME (2026-04-28, serial 110128063, value 10).
Shared port (SALT, NET): byte[54] as well, but ours only while byte[37] bit
    0x80 is clear; see flocculant_flow_rate for the routing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ...const import UNSPECIFIED_VALUE
from ..feature import Feature
from ..frames import byte_or_absent
from ..presence import NOT_PRESENT

if TYPE_CHECKING:
    from ...models import AsekoDevice
    from ..frames import V7Frame
    from ..presence import NotPresent


SHARED_PORT_IS_ALGICIDE = 0x80


class FlocculantDoseTarget(Feature):
    """v7: byte[54], on a shared port only while byte[37] routes it to flocculant."""

    field = "flocculant_dose_target"

    @override
    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | NotPresent:
        """Independent flocculant port."""
        return byte_or_absent(frame[54])

    def decode_v7_routed_by_byte37(
        self, frame: V7Frame, device: AsekoDevice
    ) -> int | NotPresent:
        """Shared third-pump port, ours only while byte[37] bit 0x80 is clear."""
        b = frame[37]
        if b == UNSPECIFIED_VALUE or b & SHARED_PORT_IS_ALGICIDE:
            return NOT_PRESENT
        return byte_or_absent(frame[54])
