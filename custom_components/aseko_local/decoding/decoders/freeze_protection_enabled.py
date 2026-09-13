"""Antifreeze master enable (Issue #136).

v7: byte[37] bit 0x80 on HOME.  Confirmed on serial 110175608 (ASIN AQUA
Home REDOX, firmware A): 0x81 with antifreeze ON, 0x41 with it OFF.  When
enabled, byte[55] shows the antifreeze threshold (4 C) instead of the normal
heating setpoint.  On SALT the same bit is the algicide routing indicator,
so only HOME profiles list this feature.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...const import UNSPECIFIED_VALUE
from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


ANTIFREEZE = 0x80


class FreezeProtectionEnabled(Feature):
    """v7: byte[37] bit 0x80."""

    field = "freeze_protection_enabled"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool | None:
        b = frame[37]
        if b == UNSPECIFIED_VALUE:
            return None
        return bool(b & ANTIFREEZE)
