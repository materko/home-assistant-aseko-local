"""Configured pool volume (m3).  v7: bytes 92-93.  v8: areqs[14]."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..feature import Feature

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frame import V7Frame, V8Frame


class PoolVolume(Feature):
    """v7: bytes 92-93.  v8: areqs[14]."""

    field = "pool_volume"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> int:
        return frame.word(92)

    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> int | None:
        return frame.get("areqs", 14)
