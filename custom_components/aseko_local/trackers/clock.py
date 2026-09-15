"""How far a unit's clock is off Home Assistant's: time change, drift, alert.

Every frame that carries the unit's own clock (``unit_clock``) is compared
with the moment Home Assistant received it:

    offset = unit clock - Home Assistant clock at reception

so a negative offset is a unit that runs late.  A v7 unit sends seconds; a v8
unit sends hour and minute only, so its reading is taken as the middle of
that minute and the offset is folded into +/-12 h (there is no date to tell
a day apart).

The published offset is the median of the last ``SAMPLES`` readings, so one
late or odd frame does not move it.

The offset is split into whole **hours** (a change of time the unit did not
follow: summer / winter time, a clock set an hour off) and **drift** (the
minutes a clock gains or loses over weeks).  One number cannot tell them
apart -- -54.5 min is a unit an hour behind that runs 5.5 min fast, or one
54.5 min slow -- but the drift moves by seconds a day and a change of time
jumps by an hour, so the split is taken against the last known drift:

    hours = round((offset - last drift) / 60 min)
    drift = offset - hours

The first split, with no drift known yet, takes the drift as under 30
minutes.  A clock moved by more than 30 minutes at once is therefore read as
a change of hours.  The coordinator stores the drift, so a restart keeps it.

``out_of_sync`` looks at the **drift** only (a missed change of time has its
own ``hour_shift``) and needs every one of the last ``SAMPLES`` readings on
the same side:

* on  -- all at least ``alert_minutes`` off;
* off -- all less than ``alert_minutes`` minus the hysteresis: a fifth of the
  limit, at most 3 minutes (12 min for the default 15, 48 s for 1 min, 177 min
  for 180), so it can always clear;
* in between it keeps what it was.  Before it has been on, anything that is
  not three readings past the limit is off: turning on always takes three.
  With fewer readings than that it is None.

Nothing is compared while no frames arrive, so an offline unit keeps its last
values instead of drifting further away from a clock that moves on.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, time
from statistics import median

from homeassistant.util import dt as dt_util

DEFAULT_ALERT_MINUTES = 15
SAMPLES = 3
_HOUR = 3600
_HALF_DAY = 12 * _HOUR
_DAY = 24 * _HOUR


def offset_seconds(unit_clock: datetime | time, received: datetime) -> float:
    """Seconds the unit's clock is ahead of ``received`` (negative: behind)."""
    if isinstance(unit_clock, datetime):
        return (unit_clock - received).total_seconds()
    local = dt_util.as_local(received)
    unit = unit_clock.hour * 3600 + unit_clock.minute * 60 + 30  # middle of the minute
    ha = local.hour * 3600 + local.minute * 60 + local.second + local.microsecond / 1e6
    return (unit - ha + _HALF_DAY) % _DAY - _HALF_DAY


class ClockTracker:
    """Offset of one unit's clock, split into hours and drift, and the alert."""

    def __init__(
        self,
        alert_minutes: float = DEFAULT_ALERT_MINUTES,
        drift_minutes: float | None = None,
    ) -> None:
        self.alert_minutes = float(alert_minutes)
        self._samples: deque[float] = deque(maxlen=SAMPLES)
        self.offset_minutes: float | None = None
        #: whole hours of the offset: a change of time the unit did not follow
        self.hour_shift: int | None = None
        #: the rest, in minutes: what the clock gained or lost
        self.drift_minutes: float | None = drift_minutes
        self.out_of_sync: bool | None = None

    @property
    def _clear_below_seconds(self) -> float:
        limit = self.alert_minutes * 60
        return limit - min(180.0, limit / 5)

    def update(self, unit_clock: datetime | time | None, received: datetime) -> None:
        """Take one frame's clock reading; None (not sent, not valid) is skipped."""
        if unit_clock is None:
            return
        self._samples.append(offset_seconds(unit_clock, received))
        offset = median(self._samples)
        last_drift = (self.drift_minutes or 0.0) * 60
        hours = round((offset - last_drift) / _HOUR)
        self.offset_minutes = round(offset / 60, 1)
        self.hour_shift = hours
        self.drift_minutes = round((offset - hours * _HOUR) / 60, 1)
        if len(self._samples) < SAMPLES:
            return
        limit = self.alert_minutes * 60
        drifts = [abs(s - hours * _HOUR) for s in self._samples]
        if all(d >= limit for d in drifts):
            self.out_of_sync = True
        elif all(d < self._clear_below_seconds for d in drifts) or (
            self.out_of_sync is None
        ):
            # the first answer is off unless three readings say otherwise
            self.out_of_sync = False
