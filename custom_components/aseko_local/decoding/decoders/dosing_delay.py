"""Delay between doses (seconds).  v7: bytes 106-107.  v8: areqs[18]."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature
from ..frame import word_or_absent

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame, V8Frame
    from ..presence import NotPresent


class DosingDelay(Feature):
    """v7: bytes 106-107.  v8: areqs[18]."""

    field = "dosing_delay"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int | NotPresent:
        return word_or_absent(frame.word_or_none(106))

    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> int | None:
        return frame.get("areqs", 18)
