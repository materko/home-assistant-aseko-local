"""The unit's own clock at the moment the frame was sent."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import homeassistant.util

from ..feature import Feature
from ..frames import decode_timestamp

if TYPE_CHECKING:
    from ...aseko_data import AsekoDevice
    from ..frames import V7Frame, V8Frame


_LOGGER = logging.getLogger(__name__)


class Timestamp(Feature):
    """v7: bytes 6-11 (year offset 2000).  v8: hour and minute only."""

    field = "timestamp"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> datetime:
        return decode_timestamp(frame.raw)

    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> datetime:
        """Today's date from Home Assistant's clock, hour and minute from ins[16:18]."""
        now = datetime.now(tz=homeassistant.util.dt.get_default_time_zone())
        hour = frame.get("ins", 16)
        minute = frame.get("ins", 17)
        if hour is None or minute is None:
            return now
        try:
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError as exc:
            _LOGGER.debug(
                "v8 frame contains invalid time %02d:%02d (%s) - using now()",
                hour,
                minute,
                exc,
            )
            return now
