"""pH setpoint.  v7: byte[52] / 10 when a pH probe is installed.  v8: areqs[0] / 10."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...aseko_data import AsekoProbeType
from ..feature import Feature
from .configuration import Configuration

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame, V8Frame


class RequiredPh(Feature):
    """v7: byte[52] / 10.  v8: areqs[0] / 10."""

    field = "required_ph"
    depends_on = (Configuration,)

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> float | None:
        if AsekoProbeType.PH not in device.configuration:
            return None
        return frame[52] / 10

    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> float | None:
        raw = frame.get("areqs", 0)
        return raw / 10 if raw is not None else None
