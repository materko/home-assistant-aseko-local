"""Whether the flocculant dosing pump is running.

v7: byte[29] bit 0x20 (confirmed on OXY: toggles exactly at the 19:33:52 floc
event; confirmed on SALT: Apr 3 frames, same bit as algicide; uncertain on
HOME and PROFI).  Reported only once the flow-rate reading shows the port is
configured for flocculant (see flowrate_floc).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature
from ..presence import NOT_PRESENT
from .flowrate_floc import FlowrateFloc

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame
    from ..presence import NotPresent


FLOC_PUMP = 0x20


class FlocPumpRunning(Feature):
    """v7: byte[29] bit 0x20, only while a flow rate is configured."""

    field = "floc_pump_running"
    depends_on = (FlowrateFloc,)

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool | NotPresent:
        if device.flowrate_floc is None:
            return NOT_PRESENT
        return bool(frame[29] & FLOC_PUMP)
