"""pH setpoint.  v7: byte[52] / 10 when a pH probe is installed.  v8: areqs[0] / 10."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ...const import UNSPECIFIED_VALUE
from ...models import AsekoProbeType
from ..feature import Feature
from ..presence import NOT_PRESENT
from .configuration import Configuration

if TYPE_CHECKING:
    from ...models import AsekoDevice
    from ..frames import V7Frame, V8Frame
    from ..presence import NotPresent


class PhTarget(Feature):
    """v7: byte[52] / 10.  v8: areqs[0] / 10."""

    field = "ph_target"
    depends_on = (Configuration,)

    @override
    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> float | NotPresent:
        if AsekoProbeType.PH not in device.configuration:
            return NOT_PRESENT
        if frame[52] == UNSPECIFIED_VALUE:
            return None  # the probe is there, the setpoint is not filled in
        return frame[52] / 10

    @override
    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> float | None:
        raw = frame.value("areqs", 0)
        return raw / 10 if raw is not None else None
