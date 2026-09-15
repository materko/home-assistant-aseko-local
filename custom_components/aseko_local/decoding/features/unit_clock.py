"""The unit's own clock as it sent it, with nothing filled in from Home Assistant.

``timestamp`` falls back to Home Assistant's clock when the unit sends none,
which is right for a "when" but useless for asking how far the unit's clock
is off.  This field keeps only what the unit sent, for ``trackers.clock``:

* v7: bytes 6-11 as a ``datetime`` (year offset 2000) in Home Assistant's
  time zone -- the unit sends wall-clock time with no zone of its own;
* v8: ``ins[16]`` / ``ins[17]`` as a ``time`` -- hour and minute, no date.

None when the bytes are unset or not a valid date.  A model that never
sends its clock (v7 NET: 0xFF on every frame) does not list the feature.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING

import homeassistant.util

from ...const import UNSPECIFIED_VALUE
from ..feature import Feature

if TYPE_CHECKING:
    from ...models import AsekoDevice
    from ..frames import V7Frame, V8Frame

YEAR_OFFSET = 2000


class UnitClock(Feature):
    """v7: bytes 6-11.  v8: ins[16] hour, ins[17] minute."""

    field = "unit_clock"

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> datetime | None:
        data = frame.raw
        if len(data) < 12 or UNSPECIFIED_VALUE in data[6:12]:
            return None
        try:
            return datetime(
                YEAR_OFFSET + data[6],
                data[7],
                data[8],
                data[9],
                data[10],
                data[11],
                tzinfo=homeassistant.util.dt.get_default_time_zone(),
            )
        except ValueError:
            return None

    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> time | None:
        hour = frame.get("ins", 16)
        minute = frame.get("ins", 17)
        if hour is None or minute is None:
            return None
        try:
            return time(hour, minute)
        except (TypeError, ValueError):
            return None
