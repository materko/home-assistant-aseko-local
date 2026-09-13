"""Measured salinity (kg/m3)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


class Salinity(Feature):
    """v7: byte[20] / 10.  On a chlorine unit the same byte is free_chlorine_mv[hi]."""

    field = "salinity"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> float:
        return frame[20] / 10
