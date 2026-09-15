"""The unit's clock against Home Assistant's: offset and the out-of-sync alert."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

import pytest

from custom_components.aseko_local.decoding import decode
from custom_components.aseko_local.trackers.clock import (
    DEFAULT_ALERT_MINUTES,
    SAMPLES,
    ClockTracker,
    offset_seconds,
)

from .test_decode_v7 import _make_base_bytes
from .test_decode_v8 import REFERENCE_FRAME

T0 = datetime(2026, 9, 14, 8, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _home_assistant_in_utc():
    """The v8 reading has no zone of its own; compare it in UTC here."""
    from homeassistant.util import dt as dt_util

    original = dt_util.DEFAULT_TIME_ZONE
    dt_util.set_default_time_zone(UTC)
    yield
    dt_util.set_default_time_zone(original)


def _feed(tracker: ClockTracker, offsets_minutes, start: datetime = T0) -> None:
    """Frames ten seconds apart whose unit clock is ``offset`` minutes off."""
    for i, minutes in enumerate(offsets_minutes):
        received = start + timedelta(seconds=10 * i)
        tracker.update(received + timedelta(minutes=minutes), received)


# ── decoding ─────────────────────────────────────────────────────────────────


def test_v7_unit_clock_is_what_the_unit_sent():
    device = decode(bytes(_make_base_bytes()))
    assert device.unit_clock == datetime(2024, 6, 15, 12, 34, 56, tzinfo=UTC)
    assert "unit_clock" in device.features


def test_v7_unit_clock_is_none_when_the_bytes_are_unset():
    data = _make_base_bytes()
    data[6:12] = b"\xff" * 6
    device = decode(bytes(data))
    assert device.unit_clock is None
    # timestamp still falls back to Home Assistant's clock; the unit clock does not
    assert device.timestamp is not None


def test_v7_net_does_not_have_a_unit_clock():
    data = _make_base_bytes()
    data[4] = 0x09  # NET, CLF probe
    data[6:12] = b"\xff" * 6
    device = decode(bytes(data))
    assert "unit_clock" not in device.possible_features


def test_v8_unit_clock_is_hour_and_minute():
    device = decode(REFERENCE_FRAME)
    assert device.unit_clock == time(22, 27)


# ── offset ───────────────────────────────────────────────────────────────────


def test_offset_of_a_unit_ahead_is_positive_and_behind_negative():
    assert offset_seconds(T0 + timedelta(minutes=5, seconds=30), T0) == 330
    assert offset_seconds(T0 - timedelta(minutes=12), T0) == -720


def test_v8_offset_takes_the_middle_of_the_minute_and_crosses_midnight():
    received = datetime(2026, 9, 14, 23, 58, 30, tzinfo=UTC)
    assert offset_seconds(time(23, 58), received) == 0
    # the unit already shows 00:03 of the next day: five minutes ahead
    assert offset_seconds(time(0, 3), received) == 300
    # and one still before midnight while HA is past it: behind
    assert offset_seconds(time(23, 50), received + timedelta(minutes=5)) == -780


def test_offset_is_the_median_so_one_odd_frame_does_not_move_it():
    tracker = ClockTracker()
    _feed(tracker, [5.5, 42.0, 5.4])
    assert tracker.offset_minutes == 5.5


def test_nothing_is_decided_before_enough_frames():
    tracker = ClockTracker()
    _feed(tracker, [30.0] * (SAMPLES - 1))
    assert tracker.offset_minutes == 30.0
    assert tracker.out_of_sync is None


def test_frames_without_a_clock_change_nothing():
    tracker = ClockTracker()
    _feed(tracker, [5.0] * SAMPLES)
    tracker.update(None, T0 + timedelta(hours=1))
    assert tracker.offset_minutes == 5.0
    assert tracker.out_of_sync is False


# ── alert ────────────────────────────────────────────────────────────────────


def test_default_limit_is_fifteen_minutes():
    assert DEFAULT_ALERT_MINUTES == 15
    assert ClockTracker().alert_minutes == 15


def test_a_small_drift_does_not_alert():
    tracker = ClockTracker()
    _feed(tracker, [5.1, 5.3, 5.5])
    assert tracker.out_of_sync is False


@pytest.mark.parametrize("minutes", [15.0, -15.0, 25.0, -29.0])
def test_past_the_limit_either_way_alerts(minutes):
    tracker = ClockTracker()
    _feed(tracker, [minutes] * SAMPLES)
    assert tracker.out_of_sync is True


def test_one_late_frame_does_not_alert():
    tracker = ClockTracker()
    _feed(tracker, [1.0, 1.0, 1.0, 20.0, 1.0])
    assert tracker.out_of_sync is False


def test_it_clears_only_below_the_hysteresis():
    tracker = ClockTracker()
    _feed(tracker, [20.0] * SAMPLES)
    assert tracker.out_of_sync is True

    _feed(tracker, [13.0] * SAMPLES, T0 + timedelta(minutes=5))  # under 15, over 12
    assert tracker.out_of_sync is True

    _feed(tracker, [11.0] * SAMPLES, T0 + timedelta(minutes=10))
    assert tracker.out_of_sync is False


@pytest.mark.parametrize("readings", [[20, 20, 0], [0, 20, 20], [-20, 0, -20]])
def test_turning_on_takes_three_readings_even_at_the_start(readings):
    """Audit K2: two readings past the limit out of three are not enough."""
    tracker = ClockTracker()
    _feed(tracker, readings)
    assert tracker.out_of_sync is False


def test_a_first_window_inside_the_band_is_off():
    tracker = ClockTracker()
    _feed(tracker, [13.0, 16.0, 13.5])
    assert tracker.out_of_sync is False


@pytest.mark.parametrize(
    ("limit", "clears_below"),
    [(1, 48), (2, 96), (10, 480), (15, 720), (30, 1620)],
)
def test_every_limit_can_clear(limit, clears_below):
    """Audit K1: the hysteresis is a fifth of the limit, at most 3 min."""
    # a drift that grew there, so the split does not read it as hours
    tracker = ClockTracker(alert_minutes=limit, drift_minutes=limit * 1.5)
    _feed(tracker, [limit * 1.5] * SAMPLES)
    assert tracker.out_of_sync is True

    # exactly on the line still counts as off the limit
    _feed(tracker, [clears_below / 60] * SAMPLES, T0 + timedelta(minutes=5))
    assert tracker.out_of_sync is True

    _feed(tracker, [0.0] * SAMPLES, T0 + timedelta(minutes=10))
    assert tracker.out_of_sync is False


def test_the_limit_can_be_set_lower():
    tracker = ClockTracker(alert_minutes=5)
    _feed(tracker, [5.1, 5.3, 5.5])
    assert tracker.out_of_sync is True
    # a fifth of the limit: off again below 4 minutes
    _feed(tracker, [4.5] * SAMPLES, T0 + timedelta(minutes=5))
    assert tracker.out_of_sync is True
    _feed(tracker, [3.9] * SAMPLES, T0 + timedelta(minutes=10))
    assert tracker.out_of_sync is False


def test_two_units_are_tracked_apart():
    ahead, fine = ClockTracker(), ClockTracker()
    _feed(ahead, [30.0] * SAMPLES)
    _feed(fine, [0.5] * SAMPLES)
    assert (ahead.out_of_sync, fine.out_of_sync) == (True, False)


# ── hours and drift ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("drift_before", "offset", "hours", "drift"),
    [
        (None, 5.5, 0, 5.5),  # first reading: drift under 30 min
        (None, 25.0, 0, 25.0),
        (None, -54.5, -1, 5.5),
        (5.5, 5.6, 0, 5.6),  # an ordinary day
        (5.5, 65.5, 1, 5.5),  # autumn change not followed
        (5.5, -54.5, -1, 5.5),  # spring change not followed
        (25.0, 31.0, 0, 31.0),  # a drift that grew past 30 min stays drift
        (5.5, 45.5, 1, -14.5),  # a clock moved 40 min at once reads as an hour
    ],
)
def test_the_offset_splits_into_hours_and_drift(drift_before, offset, hours, drift):
    tracker = ClockTracker(drift_minutes=drift_before)
    _feed(tracker, [offset] * SAMPLES)
    assert tracker.offset_minutes == offset
    assert tracker.hour_shift == hours
    assert tracker.drift_minutes == drift


def test_a_missed_change_of_time_alone_does_not_alert():
    """The alert is about drift; the hour shift has its own flag."""
    tracker = ClockTracker(drift_minutes=5.5)
    _feed(tracker, [-54.5] * SAMPLES)
    assert tracker.hour_shift == -1
    assert tracker.out_of_sync is False


def test_drift_past_the_limit_alerts_under_a_missed_change_of_time():
    tracker = ClockTracker(drift_minutes=14.0)
    _feed(tracker, [76.0] * SAMPLES)  # an hour ahead and 16 min fast
    assert (tracker.hour_shift, tracker.drift_minutes) == (1, 16.0)
    assert tracker.out_of_sync is True
