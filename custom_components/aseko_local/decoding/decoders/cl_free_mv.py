"""Raw free-chlorine probe voltage (mV)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...aseko_data import AsekoProbeType
from ..feature import Feature
from ..presence import NOT_PRESENT
from .configuration import Configuration

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame
    from ..presence import NotPresent


class ClFreeMv(Feature):
    """v7: bytes 20-21, when a CLF probe is installed."""

    field = "cl_free_mv"
    depends_on = (Configuration,)

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | NotPresent | None:
        if AsekoProbeType.CLF not in device.configuration:
            return NOT_PRESENT
        return frame.word_or_none(20)  # 0xFFFF: installed but unreadable
