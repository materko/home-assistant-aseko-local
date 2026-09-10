"""Dosing delay after startup (seconds).  v7: bytes 74-75.  v8: areqs[17]."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame, V8Frame


class DelayAfterStartup(Feature):
    """v7: bytes 74-75.  v8: areqs[17]."""

    field = "delay_after_startup"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int:
        return frame.word(74)

    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> int | None:
        return frame.get("areqs", 17)
