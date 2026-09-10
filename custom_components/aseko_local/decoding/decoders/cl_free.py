"""Measured free chlorine (mg/l)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...aseko_data import AsekoProbeType
from ..feature import Feature
from .configuration import Configuration

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


class ClFree(Feature):
    """v7: bytes 16-17 / 100, when a CLF probe is installed."""

    field = "cl_free"
    depends_on = (Configuration,)

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> float | None:
        if AsekoProbeType.CLF not in device.configuration:
            return None
        return frame.word(16) / 100
