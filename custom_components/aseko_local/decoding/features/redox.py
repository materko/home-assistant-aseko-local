"""Measured redox potential (mV)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...aseko_data import AsekoProbeType
from ...const import UNSPECIFIED_VALUE
from ..feature import Feature
from ..presence import NOT_PRESENT
from .configuration import Configuration

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frames import V7Frame, V8Frame
    from ..presence import NotPresent


class Redox(Feature):
    """v7: bytes 18-19, or bytes 16-17 when 18-19 are 0xFFFF.  v8: ains[6]."""

    field = "redox"
    depends_on = (Configuration,)

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | NotPresent | None:
        if AsekoProbeType.REDOX not in device.configuration:
            return NOT_PRESENT
        if frame[18] == UNSPECIFIED_VALUE and frame[19] == UNSPECIFIED_VALUE:
            return frame.word_or_none(16)  # 0xFFFF: installed but unreadable
        return frame.word_or_none(18)

    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> int | NotPresent:
        raw = frame.value("ains", 6)
        return NOT_PRESENT if raw is None else raw
