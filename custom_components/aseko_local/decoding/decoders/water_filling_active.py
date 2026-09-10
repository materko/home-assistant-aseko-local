"""Whether the filling valve is open.  v7: byte[29] bit 0x02 (DomSchCoding #100)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


FILLING = 0x02


class WaterFillingActive(Feature):
    """v7: byte[29] bit 0x02."""

    field = "water_filling_active"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool:
        return bool(frame[29] & FILLING)
