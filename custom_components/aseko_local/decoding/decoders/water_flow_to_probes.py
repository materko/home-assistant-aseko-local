"""Whether water is flowing past the probes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...const import WATER_FLOW_TO_PROBES
from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame, V8Frame


class WaterFlowToProbes(Feature):
    """v7: byte[28] == 0xAA.  v8: ins[8] != 0."""

    field = "water_flow_to_probes"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool:
        return frame[28] == WATER_FLOW_TO_PROBES

    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> bool | None:
        raw = frame.get("ins", 8)
        return bool(raw) if raw is not None else None
