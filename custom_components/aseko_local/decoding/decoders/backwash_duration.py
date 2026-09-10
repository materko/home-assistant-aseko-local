"""Backwash duration (seconds).  v7: byte[71] * 10.

Backwash schedule, bytes 68-71, on every model with a backwash valve.  NET
(Aqua NET) is a measurement and dosing unit with neither a filter nor a
backwash valve; before profiles, reading these bytes on every model surfaced
phantom backwash entities from a NET frame carrying non-0xFF data there
(Issue #129), so no NET profile lists them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...const import UNSPECIFIED_VALUE
from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame


class BackwashDuration(Feature):
    """v7: byte[71] * 10."""

    field = "backwash_duration"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | None:
        if frame[71] == UNSPECIFIED_VALUE:
            return None
        return frame[71] * 10
