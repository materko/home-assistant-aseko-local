"""Whether the OXY Pure (hydrogen peroxide) dosing pump is running.

v7: byte[29] bit 0x40 on ASIN AQUA Oxygen (confirmed: 2026-04-11 Winnetoux
log, 0x08 -> 0x48 with the pump on).  Reported only once the flow-rate
reading shows the port is configured (see flowrate_oxy).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature
from .flowrate_oxy import FlowrateOxy

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


OXY_PUMP = 0x40  # confirmed, 2026-04-11


class OxyPumpRunning(Feature):
    """v7: byte[29] bit 0x40, only while a flow rate is configured."""

    field = "oxy_pump_running"
    depends_on = (FlowrateOxy,)

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool | None:
        if device.flowrate_oxy is None:
            return None
        return bool(frame[29] & OXY_PUMP)
