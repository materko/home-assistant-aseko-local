"""Heating-control master enable (Issue #135).

v7: byte[37] bit 0x08 on HOME.  Confirmed on serial 110175608 (ASIN AQUA
Home REDOX, byte[4] = 0x03): 0x49 with heating ON, 0x41 with it
OFF, and on an ASIN AQUA Salt by toggling Heating control (2026-09-13).  The
same bit on every model with the byte[37] bit field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...const import UNSPECIFIED_VALUE
from ..feature import Feature

if TYPE_CHECKING:
    from ...models import AsekoDevice
    from ..frames import V7Frame


HEATING_CONTROL = 0x08


class HeatingControlEnabled(Feature):
    """v7: byte[37] bit 0x08."""

    field = "heating_control_enabled"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool | None:
        b = frame[37]
        if b == UNSPECIFIED_VALUE:
            return None
        return bool(b & HEATING_CONTROL)
