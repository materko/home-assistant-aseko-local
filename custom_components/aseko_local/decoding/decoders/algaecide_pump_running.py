"""Whether the algicide dosing pump is running.

v7: byte[29] bit 0x20 on SALT (confirmed: 27 algicide frames read 0x28 =
0x08 | 0x20, PR #87) and HOME (uncertain), bit 0x10 on OXY (confirmed:
2026-04-11 Winnetoux log, 0x08 -> 0x18 with the pump on).

On SALT the same bit also means flocculant: one physical port, configured for
either chemical.  Whether the port is set up for algicide at all is settled
by the flow-rate reading (see algaecide_flow_rate), so the pump state is only
reported once that is known.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature
from ..presence import NOT_PRESENT
from .algaecide_flow_rate import AlgaecideFlowRate

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame
    from ..presence import NotPresent


ALGICIDE_PUMP = 0x20  # SALT confirmed (PR #87), HOME uncertain
ALGICIDE_PUMP_OXY = 0x10  # confirmed, 2026-04-11


class AlgaecidePumpRunning(Feature):
    """v7: byte[29] bit 0x20 (0x10 on OXY), only while a flow rate is configured."""

    field = "algaecide_pump_running"
    depends_on = (AlgaecideFlowRate,)

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool | NotPresent:
        if device.algaecide_flow_rate is None:
            return NOT_PRESENT
        return bool(frame[29] & ALGICIDE_PUMP)

    def decode_v7_oxy(self, frame: V7Frame, device: AsekoDevice) -> bool | NotPresent:
        if device.algaecide_flow_rate is None:
            return NOT_PRESENT
        return bool(frame[29] & ALGICIDE_PUMP_OXY)
