"""Delay between doses (seconds).  v7: bytes 106-107.  v8: areqs[18]."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame, V8Frame


class DelayAfterDose(Feature):
    """v7: bytes 106-107.  v8: areqs[18]."""

    field = "delay_after_dose"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int:
        return frame.word(106)

    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> int | None:
        return frame.get("areqs", 18)
