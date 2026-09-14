"""Whether the automatic filter backwash is enabled.

v7: byte[22] bit 0x10.  Confirmed on an ASIN AQUA Salt: switching the
backwash schedule off cleared the bit together with byte[68] (interval)
dropping to 0 (2026-09-13 marked test case).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...const import UNSPECIFIED_VALUE
from ..feature import Feature
from ..presence import NOT_PRESENT

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frames import V7Frame
    from ..presence import NotPresent


MASK = 0x10


class BackwashScheduleEnabled(Feature):
    """v7: byte[22] bit 0x10."""

    field = "backwash_schedule_enabled"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool | NotPresent:
        if frame[22] == UNSPECIFIED_VALUE:
            return NOT_PRESENT
        return bool(frame[22] & MASK)
