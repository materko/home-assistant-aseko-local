"""Maximum filling-valve open time (seconds).

v7: bytes 76-77, big-endian, in seconds exactly as the unit transmits it,
matching the neighbouring delay_after_startup (74-75) and delay_after_dose
(106-107).  Verified on an ASIN AQUA Salt by changing the setting in the
Aseko Live app and re-reading the frame:

    0x0708 = 1800 -> app showed 30 min
    0x0B04 = 2820 -> app showed 47 min

Bytes 94-95 were the previous guess and are wrong: byte 95 is
flowrate_ph_minus.  0xFFFF = the device does not implement the feature
(Issue #129: a bare int would otherwise read 65535 on NET / PROFI).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


class MaxFillingTime(Feature):
    """v7: bytes 76-77, 0xFFFF = not implemented."""

    field = "max_filling_time"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | None:
        value = frame.word(76)
        return None if value == 0xFFFF else value
