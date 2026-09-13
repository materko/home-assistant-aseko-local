"""Electrolyser polarity: left, right, or waiting.

byte[29] bit 0x10 = electrolyser running (confirmed: 25 SALT frames read
0x18 = 0x08 | 0x10, PR #87).  Bit 0x40 on top of it marks the left polarity
(tentative: a single Apr 2 frame read 0x58 = 0x08 | 0x10 | 0x40).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...aseko_data import AsekoElectrolyzerDirection
from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


RUNNING_RIGHT = 0x10  # confirmed: same dataset as electrolysis_running
RUNNING_LEFT = 0x50  # tentative: single frame


class ElectrodePolarity(Feature):
    """v7: byte[29] 0x50 = left, 0x10 = right, neither = waiting."""

    field = "electrode_polarity"

    def decode_v7(
        self, frame: V7Frame, device: AsekoDevice
    ) -> AsekoElectrolyzerDirection:
        if (frame[29] & RUNNING_LEFT) == RUNNING_LEFT:
            return AsekoElectrolyzerDirection.LEFT
        if frame[29] & RUNNING_RIGHT:
            return AsekoElectrolyzerDirection.RIGHT
        return AsekoElectrolyzerDirection.WAITING
