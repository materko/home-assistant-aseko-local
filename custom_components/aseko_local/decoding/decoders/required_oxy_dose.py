"""OXY Pure dose setpoint (ml/m3/day), ASIN AQUA Oxygen only.

v7: byte[53].  The OXY firmware fills the CLF / REDOX slots with the
placeholder 0x001E, which is why no OXY profile lists those setpoints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


class RequiredOxyDose(Feature):
    """v7: byte[53]."""

    field = "required_oxy_dose"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int:
        return frame[53]
