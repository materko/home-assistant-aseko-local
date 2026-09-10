"""Water temperature setpoint (degrees C).  v7: byte[55]."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature
from ..frame import byte_or_none

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


class RequiredWaterTemperature(Feature):
    """v7: byte[55]."""

    field = "required_water_temperature"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | None:
        return byte_or_none(frame[55])
