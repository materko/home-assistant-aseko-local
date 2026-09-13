"""Whether "Flow detection" (the flow meter) is enabled in the unit's configuration.

v7: byte[37] bit 0x02.  Confirmed on an ASIN AQUA Salt: switching Flow
detection OFF cleared the bit and ON set it again (2026-09-13 marked test
cases).  On HOME the same bit was once read as a "transitional edit state".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...const import UNSPECIFIED_VALUE
from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


MASK = 0x02


class FlowDetectionEnabled(Feature):
    """v7: byte[37] bit 0x02."""

    field = "flow_detection_enabled"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool | None:
        if frame[37] == UNSPECIFIED_VALUE:
            return None  # this frame does not say
        return bool(frame[37] & MASK)
