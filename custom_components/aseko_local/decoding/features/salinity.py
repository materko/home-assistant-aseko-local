"""Measured salinity (kg/m3)."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ..feature import Feature
from ..frames import byte_or_none

if TYPE_CHECKING:
    from ...models import AsekoDevice
    from ..frames import V7Frame


class Salinity(Feature):
    """v7: byte[20] / 10; 0xFF (not filled in) reads unknown, not 25.5."""

    field = "salinity"

    @override
    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> float | None:
        value = byte_or_none(frame[20])
        return None if value is None else value / 10
