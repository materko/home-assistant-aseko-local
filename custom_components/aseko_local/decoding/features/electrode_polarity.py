"""Electrolyser polarity: left, right, or waiting.

byte[29] bit 0x10 = electrolyser running (confirmed: 25 SALT frames read
0x18 = 0x08 | 0x10, PR #87).  Bit 0x40 = right polarity, clear = left:
confirmed on an ASIN AQUA Salt by switching the electrode by hand to right
(bit set) and to left (bit clear) with a marker after each (2026-09-13).  The
earlier reading had it the other way round, from a single frame.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...models import AsekoElectrodePolarity
from ..feature import Feature

if TYPE_CHECKING:
    from ...models import AsekoDevice
    from ..frames import V7Frame


RUNNING = 0x10
RIGHT = 0x40


class ElectrodePolarity(Feature):
    """v7: byte[29] 0x10 running, then 0x40 = right, clear = left."""

    field = "electrode_polarity"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> AsekoElectrodePolarity:
        if not frame[29] & RUNNING:
            return AsekoElectrodePolarity.WAITING
        if frame[29] & RIGHT:
            return AsekoElectrodePolarity.RIGHT
        return AsekoElectrodePolarity.LEFT
