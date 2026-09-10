"""Whether the variable-speed filtration pump is on.

v7: byte[22] bit 0x08.  Confirmed on serial 110175608 (ASIN AQUA Home REDOX):
0x83 with the pump off, 0x8b with it on (any brand).  0xFF = not reported.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...const import UNSPECIFIED_VALUE
from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


VSP_PUMP = 0x08


class VspPumpRunning(Feature):
    """v7: byte[22] bit 0x08."""

    field = "vsp_pump_running"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool | None:
        if frame[22] == UNSPECIFIED_VALUE:
            return None
        return bool(frame[22] & VSP_PUMP)
