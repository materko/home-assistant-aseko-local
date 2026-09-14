"""Heating control tied to filtration ("heating is parent to filtration").

v7: byte[38] bit 0x10.  Confirmed on an ASIN AQUA Salt (2026-09-14): set with
the setting switched on, cleared with it off, heating control on throughout.
The unit offers the setting only while heating control is on, so with heating
control off the value is not present.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...const import UNSPECIFIED_VALUE
from ..feature import Feature
from ..presence import NOT_PRESENT
from .heating_control_enabled import HeatingControlEnabled

if TYPE_CHECKING:
    from ...models import AsekoDevice
    from ..frames import V7Frame
    from ..presence import NotPresent


HEATING_LINKED_TO_FILTRATION = 0x10


class HeatingLinkedToFiltration(Feature):
    """v7: byte[38] bit 0x10, only while heating control is on."""

    field = "heating_linked_to_filtration"
    depends_on = (HeatingControlEnabled,)

    def decode_v7(
        self, frame: V7Frame, device: AsekoDevice
    ) -> bool | NotPresent | None:
        if device.heating_control_enabled is False:
            return NOT_PRESENT
        b = frame[38]
        if b == UNSPECIFIED_VALUE or device.heating_control_enabled is None:
            return None
        return bool(b & HEATING_LINKED_TO_FILTRATION)
