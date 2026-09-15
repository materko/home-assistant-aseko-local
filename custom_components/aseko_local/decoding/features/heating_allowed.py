"""Whether heating is allowed right now by its time window or outside temperature.

v7: byte[78] bit 0x80.  A live state, not a setting.  Confirmed on an ASIN
AQUA Salt (2026-09-13/14 marked test cases): with a heating time window of
08:00-16:00 at 23:59 the bit cleared, with 00:00-14:50 at 00:01 it was set;
with "outside temperature above 17 C" it cleared and "below 17 C" set it,
the unit having no air probe (-40.0 C).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ..feature import Feature
from ..frames import flag_or_none

if TYPE_CHECKING:
    from ...models import AsekoDevice
    from ..frames import V7Frame


MASK = 0x80


class HeatingAllowed(Feature):
    """v7: byte[78] bit 0x80."""

    field = "heating_allowed"

    @override
    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool | None:
        return flag_or_none(frame[78], MASK)
