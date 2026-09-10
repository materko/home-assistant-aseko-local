"""Configured OXY Pure pump flow rate (ml/min).

v7: byte[99] on ASIN AQUA Oxygen (confirmed), the slot that is the chlorine
pump on every other model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature
from ..frame import byte_or_none

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


class FlowrateOxy(Feature):
    """v7: byte[99]."""

    field = "flowrate_oxy"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | None:
        return byte_or_none(frame[99])
