"""Configured algicide pump flow rate (ml/min).

Two layouts exist for the algicide / flocculant pair, and which one a model
uses is a property of the model -- so this feature offers both readings and
the profile picks:

Independent ports (OXY, HOME): flocculant at byte[101], algicide at
    byte[103].  Confirmed on OXY (2026-04-11, algicide = 60 ml/min) and on
    HOME (serials 110071590 / 110128063, Issues #110 and #115).

Shared port (SALT, NET, PROFI): one physical pump at byte[101], configured
    for either chemical.  byte[37] bit 0x80 set = algicide, clear =
    flocculant (confirmed by @hopkins-tk on SALT v7.x and consistent with
    @jmnemonicj, SALT v5.0, Issue #84).  byte[37] = 0xFF = configuration
    unknown, both stay None.
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


class FlowrateAlgicide(Feature):
    """v7: byte[103], or byte[101] when byte[37] routes the shared port to algicide."""

    field = "flowrate_algicide"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | None:
        """Independent algicide port."""
        return byte_or_none(frame[103])

    def decode_v7_routed_by_byte37(
        self, frame: V7Frame, device: AsekoDevice
    ) -> int | None:
        """Shared third-pump port, ours only while byte[37] bit 0x80 is set."""
        b = frame[37]
        if b == UNSPECIFIED_VALUE or not b & SHARED_PORT_IS_ALGICIDE:
            return None
        return byte_or_none(frame[101])
