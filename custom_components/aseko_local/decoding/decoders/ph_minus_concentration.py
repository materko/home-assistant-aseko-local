"""Configured pH-minus acid concentration (percent).

v7: byte[112], e.g. 5 -> 5 %, 10 -> 10 %.  Confirmed on serial 110175608
(ASIN AQUA Home REDOX, Issue #139).  0xFF = not reported.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature
from ..frame import byte_or_none

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


class PhMinusConcentration(Feature):
    """v7: byte[112]."""

    field = "ph_minus_concentration"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | None:
        return byte_or_none(frame[112])
