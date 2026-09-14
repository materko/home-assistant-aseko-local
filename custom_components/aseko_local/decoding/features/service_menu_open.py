"""Somebody has the unit's settings menu open.

v7: byte[37] bit 0x04.  Not a filtration state,
despite living in the same byte: it says a person is standing at the unit,
and nothing about what they are doing.  The menu is where filtration and
backwash can be started by hand, but the unit stops transmitting while it is
open, so whether anything was touched is not observable.

Confirmed on an ASIN AQUA Salt: 0xD7 / 0xF7 are P1 / P1&P2 with the menu
open, and each shows up as a brief flip to True followed by the device going
offline.  On HOME (Issue #133) it is documented as a standing
manual override that forces the pump off; see filtration_running.

On HOME the values once called "transitional edit states" (0x47 / 0x57)
are this bit; 0x02 is the Flow detection setting.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...const import UNSPECIFIED_VALUE
from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frames import V7Frame


MENU_OPEN = 0x04


class ServiceMenuOpen(Feature):
    """v7: byte[37] bit 0x04."""

    field = "service_menu_open"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool | None:
        b = frame[37]
        if b == UNSPECIFIED_VALUE:
            return None
        return bool(b & MENU_OPEN)
