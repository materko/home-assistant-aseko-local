"""Measured water temperature (degrees C)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature
from ..presence import NOT_PRESENT

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frames import V7Frame, V8Frame
    from ..presence import NotPresent


class WaterTemperature(Feature):
    """v7: bytes 25-26 / 10.  v8: ins[0] / 10."""

    field = "water_temperature"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> float | None:
        raw = frame.word_or_none(25)  # 0xFFFF: probe unreadable
        return None if raw is None else raw / 10

    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> float | NotPresent:
        raw = frame.value("ins", 0)
        return raw / 10 if raw is not None else NOT_PRESENT
