"""Timed chlorine dose (ml/m3/h), for units dosing by volume.

byte[53] carries one disinfection setpoint whose meaning depends on the
installed probes, in this order of precedence: a CLF probe makes it the
free-chlorine setpoint, otherwise a REDOX probe makes it the redox setpoint,
otherwise a DOSE probe makes it the timed chlorine dose.  Each of the three
features reads the byte and answers only when it is the one that applies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...aseko_data import AsekoProbeType
from ..feature import Feature
from .configuration import Configuration

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


class RequiredClDose(Feature):
    """v7: byte[53] with a DOSE probe and neither CLF nor REDOX."""

    field = "required_cl_dose"
    depends_on = (Configuration,)

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | None:
        probes = device.configuration
        if (
            AsekoProbeType.CLF in probes
            or AsekoProbeType.REDOX in probes
            or AsekoProbeType.DOSE not in probes
        ):
            return None
        return frame[53]
