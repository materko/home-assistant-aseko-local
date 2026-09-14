"""Whether the pH-minus dosing pump is running.

v7: byte[29] bit 0x80 (confirmed on OXY: 2026-04-12 Winnetoux log, byte[29]
0x08 -> 0x88 with the pump on; unconfirmed on SALT, uncertain on HOME and
PROFI), bit 0x01 on NET (confirmed: Issue #66).  v8: outs[8].
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frames import V7Frame, V8Frame


PH_MINUS_PUMP = 0x80
PH_MINUS_PUMP_NET = 0x01  # confirmed, Issue #66


class PhMinusPumpRunning(Feature):
    """v7: byte[29] bit 0x80, or bit 0x01 on NET.  v8: outs[8]."""

    field = "ph_minus_pump_running"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool:
        return bool(frame[29] & PH_MINUS_PUMP)

    def decode_v7_net(self, frame: V7Frame, device: AsekoDevice) -> bool:
        return bool(frame[29] & PH_MINUS_PUMP_NET)

    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> bool | None:
        raw = frame.get("outs", 8)
        return bool(raw) if raw is not None else None
