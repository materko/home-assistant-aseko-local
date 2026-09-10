"""Whether the electrolyser is running.

byte[29] bit 0x10 = electrolyser running (confirmed: 25 SALT frames read
0x18 = 0x08 | 0x10, PR #87).  Bit 0x40 on top of it marks the left polarity
(tentative: a single Apr 2 frame read 0x58 = 0x08 | 0x10 | 0x40).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


ELECTROLYZER_RUNNING = 0x10


class ElectrolyzerActive(Feature):
    """v7: byte[29] bit 0x10."""

    field = "electrolyzer_active"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool:
        return bool(frame[29] & ELECTROLYZER_RUNNING)
