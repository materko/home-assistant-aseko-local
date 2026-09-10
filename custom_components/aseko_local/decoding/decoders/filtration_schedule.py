"""The filtration schedule the unit is configured for (Issue #133).

What the unit runs when nobody is at it, read from byte[37].  Two encodings
of that byte exist, and which one a frame uses is a property of the model
and firmware -- so this feature offers both and the profile picks.

Bit flags (SALT, OXY, PROFI, HOME firmware B):
    bit 0x10 = period 1 enabled, bit 0x20 = period 2 enabled.
    0x00 = nonstop 24h, 0x10 = period 1, 0x30 = periods 1 and 2.
    0x20 without 0x10 has never been seen -- period 2 is only offered on
    top of period 1 -- and leaves the schedule unset rather than guessed.
    Confirmed on an ASIN AQUA Salt in both directions of every transition:
    0xC3 = nonstop, 0xD3 = P1, 0xF3 = P1&P2 (the high nibble carries the
    algicide routing bit 0x80 and an always-set 0x40).  Confirmed on HOME
    firmware B, serial 110169464: 0x01 = nonstop, 0x11 = P1, 0x31 = P1&P2.

Exact values (HOME firmware A, serial 110128063, byte[4] = 0x02):
    0x43 = nonstop 24h, 0x53 = timer (P1 or P1&P2, indistinguishable),
    0x47 / 0x57 = transitional edit state (bit 0x02) -> unknown.
    Any other value (Issue #135: serial 110175608 reads 0x45 / 0x49 / 0x41)
    falls back to the period bytes 56-63: no period 1 configured = nonstop,
    period 2 configured or bit 0x20 = P1&P2, else P1.

The settings-menu bit 0x04 lives in the same byte but is a different fact;
see service_menu_open.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...aseko_data import AsekoFiltrationSchedule
from ...const import FILTRATION_PERIOD2_ENABLED_MASK, UNSPECIFIED_VALUE
from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


PERIOD_BITS = 0x30
_BY_PERIOD_BITS = {
    0x00: AsekoFiltrationSchedule.NONSTOP_24H,
    0x10: AsekoFiltrationSchedule.TIMER_PERIOD_1,
    0x30: AsekoFiltrationSchedule.TIMER_PERIOD_1_AND_2,
}

HOME_A_NONSTOP = 0x43
HOME_A_TIMER = 0x53
HOME_A_TRANSITIONAL = 0x02  # 0x47 / 0x57: the schedule is being edited


class FiltrationSchedule(Feature):
    """v7: byte[37] bits 0x10 / 0x20, or exact values on HOME firmware A."""

    field = "filtration_schedule"

    def decode_v7(
        self, frame: V7Frame, device: AsekoDevice
    ) -> AsekoFiltrationSchedule | None:
        """Bit flags: 0x10 period 1, 0x20 period 2."""
        b = frame[37]
        if b == UNSPECIFIED_VALUE:
            return None
        return _BY_PERIOD_BITS.get(b & PERIOD_BITS)

    def decode_v7_home_a(
        self, frame: V7Frame, device: AsekoDevice
    ) -> AsekoFiltrationSchedule | None:
        """Exact byte values, with the period bytes as a fallback."""
        b = frame[37]
        if b == UNSPECIFIED_VALUE:
            return None
        if b == HOME_A_NONSTOP:
            return AsekoFiltrationSchedule.NONSTOP_24H
        if b == HOME_A_TIMER:
            return AsekoFiltrationSchedule.TIMER_PERIOD_1_AND_2
        if b & HOME_A_TRANSITIONAL:
            return None

        period_1_set = frame[56] != UNSPECIFIED_VALUE and frame[57] != UNSPECIFIED_VALUE
        period_2_set = frame[60] != UNSPECIFIED_VALUE and frame[61] != UNSPECIFIED_VALUE
        if not period_1_set:
            return AsekoFiltrationSchedule.NONSTOP_24H
        if period_2_set or b & FILTRATION_PERIOD2_ENABLED_MASK:
            return AsekoFiltrationSchedule.TIMER_PERIOD_1_AND_2
        return AsekoFiltrationSchedule.TIMER_PERIOD_1
