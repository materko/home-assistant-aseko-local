"""Electrolyser output (g/h), as the unit sends it.

v7: byte[21].  Confirmed on an ASIN AQUA Salt against the app and the unit
display (2026-09-11).  The unit sends 0 while the electrolyser is off
(byte[29] bit 0x10 clear) in almost every frame, but not in all of them: in
6 568 stopped frames of the marked test cases 18 carried 3-25 g/h, and 10 of
423 running frames carried 0, around a start or a stop.  The value is
reported as sent; electrolysis_running is its own entity.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ..feature import Feature
from ..frames import byte_or_none

if TYPE_CHECKING:
    from ...models import AsekoDevice
    from ..frames import V7Frame


class ChlorineProduction(Feature):
    """v7: byte[21]; 0xFF reads unknown."""

    field = "chlorine_production"

    @override
    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | None:
        return byte_or_none(frame[21])
