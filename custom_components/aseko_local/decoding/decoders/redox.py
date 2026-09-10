"""Measured redox potential (mV)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...aseko_data import AsekoProbeType
from ...const import UNSPECIFIED_VALUE
from ..feature import Feature
from .configuration import Configuration

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame, V8Frame


class Redox(Feature):
    """v7: bytes 18-19, or bytes 16-17 when 18-19 are 0xFFFF.  v8: ains[6]."""

    field = "redox"
    depends_on = (Configuration,)

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | None:
        if AsekoProbeType.REDOX not in device.configuration:
            return None
        if frame[18] == UNSPECIFIED_VALUE and frame[19] == UNSPECIFIED_VALUE:
            return frame.word(16)
        return frame.word(18)

    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> int | None:
        return frame.value("ains", 6)
