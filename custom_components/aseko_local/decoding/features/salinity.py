"""Measured salinity (kg/m3)."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ...const import UNSPECIFIED_VALUE
from ..feature import Feature

if TYPE_CHECKING:
    from ...models import AsekoDevice
    from ..frames import V7Frame


class Salinity(Feature):
    """v7: byte[20] / 10; 0xFF (not filled in) reads unknown, not 25.5."""

    field = "salinity"

    @override
    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> float | None:
        if frame[20] == UNSPECIFIED_VALUE:
            return None
        return frame[20] / 10
