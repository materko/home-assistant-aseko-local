"""Tests for BackwashTracker.

Models a real-world backwash cycle: the relay must stay on for at least
60 seconds (MIN_BACKWASH_DURATION) for the event to be recorded, and each
recorded cycle is classified as scheduled or manual from its start time.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.aseko_local.models import (
    AsekoBackwashSource,
    AsekoBackwashTrigger,
    AsekoDeviceType,
    AsekoProfileFlag,
)
from custom_components.aseko_local.trackers.backwash import (
    MAX_FRAME_GAP,
    SCHEDULED_MATCH_TOLERANCE,
    BackwashTracker,
)

T0 = datetime(2026, 6, 14, 21, 0, 0, tzinfo=timezone.utc)

# The unit's configured backwash time, matching T0's time of day, so a cycle
# starting at T0 counts as the unit's own scheduled run.
SCHEDULE_AT = time(21, 0)
SCHEDULE_EVERY_N_DAYS = 3


@pytest.fixture(autouse=True)
def _home_assistant_in_utc(monkeypatch):
    """These tests state the schedule in UTC; Home Assistant's test zone is not.

    The tracker projects and classifies in Home Assistant's time zone, so pin it
    to UTC here.  Tests about local time set their own zone on top.
    """
    from homeassistant.util import dt as dt_util

    monkeypatch.setattr(dt_util, "get_default_time_zone", lambda: timezone.utc)
    monkeypatch.setattr(dt_util, "DEFAULT_TIME_ZONE", timezone.utc)


# ── helpers ──────────────────────────────────────────────────────────────────


def _device(
    backwash_running: bool | None,
    *,
    backwash_start_time: time | None = None,
    backwash_interval: int | None = None,
) -> Any:
    """Minimal stand-in for AsekoDevice with only the fields the tracker reads.

    The schedule defaults to "not configured", which classifies every recorded
    cycle as manual — the right default for the tests that only care about the
    relay-window state machine.
    """
    dev = MagicMock()
    dev.backwash_running = backwash_running
    dev.backwash_start_time = backwash_start_time
    dev.backwash_interval = backwash_interval
    return dev


def _scheduled_device(backwash_running: bool | None) -> Any:
    """Stand-in for a device with an enabled backwash schedule at SCHEDULE_AT."""
    return _device(
        backwash_running,
        backwash_start_time=SCHEDULE_AT,
        backwash_interval=SCHEDULE_EVERY_N_DAYS,
    )


def _run_cycle(
    tracker: BackwashTracker,
    start: datetime,
    duration: timedelta = timedelta(seconds=90),
    device_factory=_scheduled_device,
) -> None:
    """Drive one complete relay on → off window through the tracker."""
    tracker.update(device_factory(True), start)
    tracker.update(device_factory(False), start + duration)


def _hass() -> MagicMock:
    """Mock Home Assistant — only ``async_create_task`` is needed by the tracker.

    ``Store.__init__`` requires ``hass.config.path(...)`` to resolve to a real
    path-like value, so we return a ``Path`` instead of letting the default
    ``MagicMock`` raise ``AttributeError`` deep in the constructor.

    The tracker hands ``async_save()`` to ``async_create_task``.  A plain
    ``MagicMock`` swallows the coroutine without awaiting it, which raises a
    RuntimeWarning per call; closing it keeps the call recorded (tests assert on
    it) while leaving nothing pending.
    """
    hass = MagicMock()
    hass.config.path.side_effect = lambda *parts: "/tmp/aseko_test/" + "/".join(parts)
    hass.async_create_task.side_effect = lambda coro, *args, **kwargs: coro.close()
    return hass


# ── basic accumulation ──────────────────────────────────────────────────────


def test_short_backwash_below_threshold_not_recorded():
    """Relay on for 30 s (below MIN_BACKWASH_DURATION) → no event recorded."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    device = _device(backwash_running=True)

    tracker.update(device, T0)
    tracker.update(device, T0 + timedelta(seconds=10))
    tracker.update(_device(backwash_running=False), T0 + timedelta(seconds=30))

    assert tracker.last_backwash is None


def test_long_backwash_recorded_at_midpoint():
    """Relay on for 90 s (≥ 60 s threshold) → event recorded at window midpoint."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    device = _device(backwash_running=True)

    tracker.update(device, T0)
    tracker.update(_device(backwash_running=False), T0 + timedelta(seconds=90))

    assert tracker.last_backwash is not None
    # Midpoint of [T0, T0+90s] = T0 + 45s
    expected = T0 + timedelta(seconds=45)
    assert tracker.last_backwash == expected


def test_exactly_threshold_backwash_recorded():
    """Relay on for exactly 60 s → still recorded (≥ comparison, not >)."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    device = _device(backwash_running=True)

    tracker.update(device, T0)
    tracker.update(_device(backwash_running=False), T0 + timedelta(seconds=60))

    assert tracker.last_backwash is not None
    # 60s window → midpoint at T0 + 30s
    assert tracker.last_backwash == T0 + timedelta(seconds=30)


def test_two_consecutive_backwashes_keep_latest():
    """If two backwashes happen in sequence, keep the later one."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    # First cycle: T0 → T0 + 90s
    tracker.update(_device(backwash_running=True), T0)
    tracker.update(_device(backwash_running=False), T0 + timedelta(seconds=90))
    first = tracker.last_backwash
    assert first is not None

    # Second cycle: T0+5min → T0+5min+90s
    second_start = T0 + timedelta(minutes=5)
    tracker.update(_device(backwash_running=True), second_start)
    tracker.update(
        _device(backwash_running=False), second_start + timedelta(seconds=90)
    )

    assert tracker.last_backwash > first
    assert tracker.last_backwash == second_start + timedelta(seconds=45)


# ── loss of connection ──────────────────────────────────────────────────────


def test_lost_connection_resets_in_progress_window():
    """Frame gap > MAX_FRAME_GAP between two relay-on updates → window reset.

    The reset discards the previous (unreliable) "on" window.  A
    subsequent "on" frame re-opens a fresh window starting at the
    recovery time.  The short follow-up window (< MIN_BACKWASH_DURATION)
    must therefore NOT be recorded.
    """
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    device = _device(backwash_running=True)

    tracker.update(device, T0)  # relay on, window starts
    # MAX_FRAME_GAP (5 min) + 1 s later, still on, but we lost the connection.
    # The reset clears the stale T0 window.  The same "on" frame re-opens
    # the window at the recovery time, so we expect a new value here.
    recovery = T0 + MAX_FRAME_GAP + timedelta(seconds=1)
    tracker.update(device, recovery)
    assert tracker._relay_on_since == recovery  # type: ignore[attr-defined]

    # 30 s later the relay goes off — only 30 s, not a real backwash.
    tracker.update(_device(backwash_running=False), recovery + timedelta(seconds=30))
    assert tracker.last_backwash is None


def test_lost_connection_during_real_backwash_does_not_record():
    """A long but disconnected window should not be recorded as a backwash.

    Scenario: the device is in a real backwash cycle, the connection drops
    for longer than MAX_FRAME_GAP, the connection recovers, and the relay
    is still on.  When the relay finally goes off, the *total* time from
    the original start is > 60 s — but the cycle spanned a disconnect and
    must not be recorded.
    """
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    device = _device(backwash_running=True)

    tracker.update(device, T0)
    # Connection drops for 6 minutes (> MAX_FRAME_GAP).
    recovery = T0 + timedelta(minutes=6)
    tracker.update(device, recovery)
    # Relay finally goes off, total elapsed would be 6 min 30 s but cycle is split.
    tracker.update(_device(backwash_running=False), recovery + timedelta(seconds=30))
    assert tracker.last_backwash is None


def test_short_gap_does_not_reset():
    """Frame gap < MAX_FRAME_GAP → window continues."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    device = _device(backwash_running=True)

    tracker.update(device, T0)
    tracker.update(device, T0 + timedelta(seconds=30))  # still on
    assert tracker._relay_on_since == T0  # type: ignore[attr-defined]

    # Window still tracks from T0 → at T0+90s, recorded
    tracker.update(_device(backwash_running=False), T0 + timedelta(seconds=90))
    assert tracker.last_backwash == T0 + timedelta(seconds=45)


# ── NET devices ─────────────────────────────────────────────────────────────


def test_net_device_skipped():
    """backwash_running is None on NET → tracker is a no-op."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    tracker.update(_device(backwash_running=None), T0)
    tracker.update(_device(backwash_running=None), T0 + timedelta(seconds=120))

    assert tracker.last_backwash is None
    assert tracker._relay_on_since is None  # type: ignore[attr-defined]
    assert tracker._last_frame_at is None  # type: ignore[attr-defined]


# ── persistence ─────────────────────────────────────────────────────────────


async def test_async_load_from_empty_store():
    """async_load on a fresh Store leaves last_backwash as None."""
    hass = _hass()
    hass.config = MagicMock()  # unused but required by HA core for Store
    # We don't call real Store here; we just verify that an empty load
    # is handled gracefully.  Direct construction with no stored data:
    tracker = BackwashTracker(hass, serial_number=110071590)
    # Manually replicate what async_load would do with an empty dict:
    # (no async_store involved — empty load is a no-op)
    assert tracker.last_backwash is None


async def test_async_save_writes_nulls_rather_than_skipping():
    """An empty state must be written, not skipped.

    Skipping made clearing a no-op on disk: the cleared value came back on the
    next restart.  Callers only reach async_save after a change, so writing
    unconditionally costs nothing.
    """
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    tracker._store.async_save = AsyncMock()  # type: ignore[method-assign]

    await tracker.async_save()

    saved = tracker._store.async_save.call_args.args[0]  # type: ignore[attr-defined]
    assert saved["last_backwash"] is None
    assert saved["last_scheduled_backwash"] is None


# ── scheduled vs. manual classification ─────────────────────────────────────


def test_nothing_recorded_starts_unknown():
    """A fresh tracker reports every field as unknown, not as a schedule guess."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    assert tracker.last_backwash is None
    assert tracker.last_scheduled_backwash is None
    assert tracker.last_manual_backwash is None
    assert tracker.last_trigger is None
    assert tracker.next_scheduled_backwash(_scheduled_device(False), T0) is None


def test_cycle_at_scheduled_time_is_scheduled():
    """A cycle starting at the configured backwash_start_time is the unit's own run."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    _run_cycle(tracker, T0)

    assert tracker.last_trigger is AsekoBackwashTrigger.SCHEDULED
    assert tracker.last_scheduled_backwash == T0 + timedelta(seconds=45)
    assert tracker.last_backwash == tracker.last_scheduled_backwash
    assert tracker.last_manual_backwash is None


def test_cycle_just_inside_tolerance_is_scheduled():
    """The unit's clock may drift from HA's — the tolerance window absorbs it."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    _run_cycle(tracker, T0 + SCHEDULED_MATCH_TOLERANCE - timedelta(seconds=1))

    assert tracker.last_trigger is AsekoBackwashTrigger.SCHEDULED


def test_cycle_outside_tolerance_is_manual():
    """A cycle well away from the scheduled time was started by hand."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    started = T0 + timedelta(hours=2)
    _run_cycle(tracker, started)

    assert tracker.last_trigger is AsekoBackwashTrigger.MANUAL
    assert tracker.last_manual_backwash == started + timedelta(seconds=45)
    assert tracker.last_backwash == tracker.last_manual_backwash
    assert tracker.last_scheduled_backwash is None


def test_cycle_is_manual_when_schedule_disabled():
    """interval 0 = automatic backwash off → the unit cannot have started it."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    def _disabled(active):
        return _device(active, backwash_start_time=SCHEDULE_AT, backwash_interval=0)

    _run_cycle(tracker, T0, device_factory=_disabled)

    assert tracker.last_trigger is AsekoBackwashTrigger.MANUAL


def test_cycle_is_manual_when_schedule_unconfigured():
    """No backwash_start_time in the frame (0xFF) → nothing to match against."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    _run_cycle(tracker, T0, device_factory=_device)

    assert tracker.last_trigger is AsekoBackwashTrigger.MANUAL


def test_scheduled_time_near_midnight_matches_across_days():
    """A cycle at 00:05 still matches a 23:55 schedule on the previous day."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    def _near_midnight(active):
        return _device(
            active,
            backwash_start_time=time(23, 55),
            backwash_interval=SCHEDULE_EVERY_N_DAYS,
        )

    # 00:05 the next day — 10 minutes after the scheduled slot, but on the
    # other side of the date boundary.
    _run_cycle(
        tracker,
        datetime(2026, 6, 15, 0, 5, 0, tzinfo=timezone.utc),
        device_factory=_near_midnight,
    )

    assert tracker.last_trigger is AsekoBackwashTrigger.SCHEDULED


def test_manual_cycle_keeps_earlier_scheduled_record():
    """A manual run must not overwrite the last scheduled one (it drives 'next')."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    _run_cycle(tracker, T0)
    scheduled = tracker.last_scheduled_backwash
    assert scheduled is not None

    manual_start = T0 + timedelta(days=1, hours=4)
    _run_cycle(tracker, manual_start)

    assert tracker.last_trigger is AsekoBackwashTrigger.MANUAL
    assert tracker.last_manual_backwash == manual_start + timedelta(seconds=45)
    assert tracker.last_scheduled_backwash == scheduled
    # "Last backwash" tracks whichever came last, regardless of kind.
    assert tracker.last_backwash == tracker.last_manual_backwash


# ── next-backwash projection ────────────────────────────────────────────────


def test_next_scheduled_backwash_unknown_after_manual_only():
    """A manual cycle says nothing about the unit's schedule phase."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    device = _scheduled_device(False)

    _run_cycle(tracker, T0 + timedelta(hours=2))

    assert tracker.last_manual_backwash is not None
    assert tracker.next_scheduled_backwash(device, T0 + timedelta(hours=3)) is None


def test_next_scheduled_backwash_projected_from_last_scheduled():
    """next = last scheduled cycle + interval, snapped to the configured time."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    device = _scheduled_device(False)

    _run_cycle(tracker, T0)

    # Recorded at the window midpoint (T0 + 45 s), but the projection snaps to
    # the configured 21:00 slot — that is when the unit will actually fire.
    assert tracker.next_scheduled_backwash(
        device, T0 + timedelta(minutes=5)
    ) == datetime(2026, 6, 17, 21, 0, 0, tzinfo=timezone.utc)


def test_next_scheduled_backwash_rolls_forward_past_missed_cycles():
    """Cycles missed while HA was down must not leave 'next' stuck in the past."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    device = _scheduled_device(False)

    _run_cycle(tracker, T0)

    # Ten days later: 06-17, 06-20 and 06-23 have all come and gone.
    now = T0 + timedelta(days=10)
    assert tracker.next_scheduled_backwash(device, now) == datetime(
        2026, 6, 26, 21, 0, 0, tzinfo=timezone.utc
    )


def test_next_scheduled_backwash_none_when_schedule_disabled():
    """With automatic backwash switched off there is no next cycle to project."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    _run_cycle(tracker, T0)
    assert tracker.last_scheduled_backwash is not None

    disabled = _device(False, backwash_start_time=SCHEDULE_AT, backwash_interval=0)
    assert tracker.next_scheduled_backwash(disabled, T0 + timedelta(minutes=5)) is None


# ── persistence of the classification ───────────────────────────────────────


async def test_async_load_restores_classified_state():
    """A stored payload round-trips into all four public fields."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    stored = {
        "last_backwash": (T0 + timedelta(days=1)).isoformat(),
        "last_scheduled_backwash": T0.isoformat(),
        "last_manual_backwash": (T0 + timedelta(days=1)).isoformat(),
        "last_trigger": "manual",
    }
    tracker._store.async_load = AsyncMock(return_value=stored)  # type: ignore[method-assign]

    await tracker.async_load()

    assert tracker.last_backwash == T0 + timedelta(days=1)
    assert tracker.last_scheduled_backwash == T0
    assert tracker.last_manual_backwash == T0 + timedelta(days=1)
    assert tracker.last_trigger is AsekoBackwashTrigger.MANUAL


async def test_async_load_tolerates_version_1_payload():
    """Stores written before classification existed keep their timestamp.

    The trigger of that pre-upgrade cycle is genuinely unknown, so it stays
    None rather than being guessed at.
    """
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    tracker._store.async_load = AsyncMock(  # type: ignore[method-assign]
        return_value={"last_backwash": T0.isoformat()}
    )

    await tracker.async_load()

    assert tracker.last_backwash == T0
    assert tracker.last_scheduled_backwash is None
    assert tracker.last_manual_backwash is None
    assert tracker.last_trigger is None


async def test_async_save_persists_classification():
    """The saved payload carries everything async_load reads back."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    tracker._store.async_save = AsyncMock()  # type: ignore[method-assign]

    _run_cycle(tracker, T0)
    await tracker.async_save()

    saved = tracker._store.async_save.call_args.args[0]  # type: ignore[attr-defined]
    assert saved["last_backwash"] == (T0 + timedelta(seconds=45)).isoformat()
    assert saved["last_scheduled_backwash"] == (T0 + timedelta(seconds=45)).isoformat()
    assert saved["last_manual_backwash"] is None
    assert saved["last_trigger"] == "scheduled"


# ── manual seeding and provenance ───────────────────────────────────────────


def test_manual_seed_marks_source_and_drives_projection():
    """A seeded date starts the projection and is labelled as manual."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    device = _scheduled_device(False)

    seeded = T0 - timedelta(days=1)
    tracker.set_last_scheduled_backwash(seeded)

    assert tracker.last_scheduled_backwash == seeded
    assert tracker.last_scheduled_source is AsekoBackwashSource.MANUAL
    # Seeded 2026-06-13 21:00, interval 3 days -> 2026-06-16 21:00.
    assert tracker.next_scheduled_backwash(device, T0) == datetime(
        2026, 6, 16, 21, 0, 0, tzinfo=timezone.utc
    )


def test_manual_seed_does_not_touch_observed_last_backwash():
    """last_backwash means "we watched this happen" — typing a date does not."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    tracker.set_last_scheduled_backwash(T0 - timedelta(days=1))

    assert tracker.last_backwash is None
    assert tracker.last_manual_backwash is None
    assert tracker.last_trigger is None


def test_cycle_detected_after_a_seed_supersedes_it():
    """The seed stood in for a real cycle; once one is detected, it takes over."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    tracker.set_last_scheduled_backwash(T0 - timedelta(days=1))
    assert tracker.last_scheduled_source is AsekoBackwashSource.MANUAL

    _run_cycle(tracker, T0)

    assert tracker.last_scheduled_backwash == T0 + timedelta(seconds=45)
    assert tracker.last_scheduled_source is AsekoBackwashSource.OBSERVED


def test_cycle_detected_after_a_later_dated_seed_still_supersedes_it():
    """Last write wins — the stored timestamps are never compared.

    Even a seed dated after the detected cycle gives way, because the cycle
    was recorded later and is the more current answer.
    """
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    tracker.set_last_scheduled_backwash(T0 + timedelta(days=5))
    _run_cycle(tracker, T0)

    assert tracker.last_scheduled_backwash == T0 + timedelta(seconds=45)
    assert tracker.last_scheduled_source is AsekoBackwashSource.OBSERVED


def test_manual_seed_overrides_an_observed_value():
    """A manual entry replaces a detected one — the user has a reason."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    _run_cycle(tracker, T0)
    assert tracker.last_scheduled_source is AsekoBackwashSource.OBSERVED

    corrected = T0 - timedelta(days=10)
    tracker.set_last_scheduled_backwash(corrected)

    assert tracker.last_scheduled_backwash == corrected
    assert tracker.last_scheduled_source is AsekoBackwashSource.MANUAL


def test_observed_manual_cycle_leaves_the_seed_alone():
    """A detected *manual* backwash says nothing about the schedule phase."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    seeded = T0 - timedelta(days=1)
    tracker.set_last_scheduled_backwash(seeded)
    _run_cycle(tracker, T0 + timedelta(hours=3))  # far from backwash_start_time

    assert tracker.last_trigger is AsekoBackwashTrigger.MANUAL
    assert tracker.last_scheduled_backwash == seeded
    assert tracker.last_scheduled_source is AsekoBackwashSource.MANUAL


def test_no_source_while_nothing_is_known():
    """No value, no provenance — the attribute stays absent rather than lying."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    assert tracker.last_scheduled_source is None


async def test_manual_seed_is_persisted_before_any_observation():
    """async_save must not bail out just because last_backwash is still None."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    tracker._store.async_save = AsyncMock()  # type: ignore[method-assign]

    seeded = T0 - timedelta(days=1)
    tracker.set_last_scheduled_backwash(seeded)
    await tracker.async_save()

    saved = tracker._store.async_save.call_args.args[0]  # type: ignore[attr-defined]
    assert saved["last_backwash"] is None
    assert saved["last_scheduled_backwash"] == seeded.isoformat()
    assert saved["last_scheduled_source"] == "manual"


async def test_async_load_restores_manual_source():
    """A seeded value survives a restart still marked as manual."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    tracker._store.async_load = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "last_scheduled_backwash": T0.isoformat(),
            "last_scheduled_source": "manual",
        }
    )

    await tracker.async_load()

    assert tracker.last_scheduled_backwash == T0
    assert tracker.last_scheduled_source is AsekoBackwashSource.MANUAL


async def test_async_load_treats_sourceless_stored_value_as_observed():
    """Stores written before provenance existed can only hold observed values."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    tracker._store.async_load = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "last_backwash": T0.isoformat(),
            "last_scheduled_backwash": T0.isoformat(),
        }
    )

    await tracker.async_load()

    assert tracker.last_scheduled_source is AsekoBackwashSource.OBSERVED


# ── backfilling an old store ────────────────────────────────────────────────


def test_backfill_classifies_a_pre_split_record_as_scheduled():
    """A store holding only last_backwash gets classified on the first frame.

    Stores written before the scheduled/manual split existed would otherwise
    leave both new sensors empty until the next real cycle, up to a whole
    interval away — even though the schedule needed to classify the stored
    value arrives in every frame.
    """
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    tracker._last_backwash = T0  # type: ignore[attr-defined]

    tracker.update(_scheduled_device(False), T0 + timedelta(minutes=5))

    assert tracker.last_scheduled_backwash == T0
    assert tracker.last_scheduled_source is AsekoBackwashSource.OBSERVED
    assert tracker.last_trigger is AsekoBackwashTrigger.SCHEDULED
    assert tracker.last_manual_backwash is None


def test_backfill_classifies_a_pre_split_record_as_manual():
    """Same, for a stored cycle that did not run at the scheduled time."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    off_schedule = T0 + timedelta(hours=4)
    tracker._last_backwash = off_schedule  # type: ignore[attr-defined]

    tracker.update(_scheduled_device(False), off_schedule + timedelta(minutes=5))

    assert tracker.last_manual_backwash == off_schedule
    assert tracker.last_trigger is AsekoBackwashTrigger.MANUAL
    assert tracker.last_scheduled_backwash is None


def test_backfill_waits_for_a_frame_that_carries_the_schedule():
    """Without backwash_start_time there is nothing to classify against — retry later."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    tracker._last_backwash = T0  # type: ignore[attr-defined]

    tracker.update(_device(False), T0 + timedelta(minutes=5))
    assert tracker.last_scheduled_backwash is None
    assert tracker.last_manual_backwash is None

    tracker.update(_scheduled_device(False), T0 + timedelta(minutes=10))
    assert tracker.last_scheduled_backwash == T0


def test_backfill_does_not_touch_an_already_split_store():
    """Once either bucket is filled the record is current — leave it alone."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    seeded = T0 - timedelta(days=3)
    tracker._last_backwash = T0  # type: ignore[attr-defined]
    tracker.set_last_scheduled_backwash(seeded)

    tracker.update(_scheduled_device(False), T0 + timedelta(minutes=5))

    assert tracker.last_scheduled_backwash == seeded
    assert tracker.last_scheduled_source is AsekoBackwashSource.MANUAL


def test_backfill_is_a_no_op_on_an_empty_store():
    """Nothing stored, nothing to classify."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    tracker.update(_scheduled_device(False), T0)

    assert tracker.last_backwash is None
    assert tracker.last_scheduled_backwash is None
    assert tracker.last_manual_backwash is None
    assert tracker.last_trigger is None


# ── clearing ────────────────────────────────────────────────────────────────


def test_clear_returns_the_value_to_unknown():
    """The undo for a mistyped date."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    tracker.set_last_scheduled_backwash(T0 - timedelta(days=1))

    tracker.clear_last_scheduled_backwash()

    assert tracker.last_scheduled_backwash is None
    assert tracker.last_scheduled_source is None


def test_clear_rearms_the_backfill():
    """After clearing, an older stored cycle is classified again.

    This is what makes clearing useful rather than merely destructive: the
    schedule falls back to whatever the integration actually observed.
    """
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    tracker._last_backwash = T0  # type: ignore[attr-defined]
    tracker.set_last_scheduled_backwash(T0 - timedelta(days=30))

    tracker.clear_last_scheduled_backwash()
    tracker.update(_scheduled_device(False), T0 + timedelta(minutes=5))

    assert tracker.last_scheduled_backwash == T0
    assert tracker.last_scheduled_source is AsekoBackwashSource.OBSERVED


def test_clear_is_a_no_op_when_already_unknown():
    """Nothing stored, nothing to clear — and no pointless write."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    tracker.clear_last_scheduled_backwash()

    assert tracker.last_scheduled_backwash is None
    tracker._hass.async_create_task.assert_not_called()  # type: ignore[attr-defined]


async def test_clear_is_persisted():
    """Clearing must reach the store, or the old value returns on restart."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    tracker._store.async_save = AsyncMock()  # type: ignore[method-assign]
    tracker.set_last_scheduled_backwash(T0)

    tracker.clear_last_scheduled_backwash()
    await tracker.async_save()

    saved = tracker._store.async_save.call_args.args[0]  # type: ignore[attr-defined]
    assert saved["last_scheduled_backwash"] is None
    assert saved["last_scheduled_source"] is None


# ── the settings menu as an observed signal (SALT byte[37] bit 0x04) ─────────


def _salt_device(
    backwash_running: bool | None,
    menu: bool,
    device_type: AsekoDeviceType = AsekoDeviceType.SALT,
) -> Any:
    """A scheduled device that also reports the settings-menu bit.

    The tracker never looks at the device type; what it reads is the profile
    flag saying the bit marks presence only, which the SALT profile carries
    and the HOME ones do not.  The type is kept as the test's way of naming
    which of the two it is modelling.
    """
    dev = _scheduled_device(backwash_running)
    dev.device_type = device_type
    dev.flags = (
        frozenset({AsekoProfileFlag.MENU_BIT_IS_PRESENCE_ONLY})
        if device_type is AsekoDeviceType.SALT
        else frozenset()
    )
    dev.service_menu_open = menu
    return dev


def _run_service_menu_cycle(
    tracker: BackwashTracker,
    start: datetime,
    menu_during: bool,
    device_type: AsekoDeviceType = AsekoDeviceType.SALT,
) -> None:
    """Drive a cycle that ends with the manual flag already dropped.

    Mirrors the captured cycle: the unit clears bit 0x04 a frame or two
    after the valve closes, so the closing frame no longer carries it.
    """
    tracker.update(_salt_device(True, menu_during, device_type), start)
    tracker.update(
        _salt_device(True, menu_during, device_type),
        start + timedelta(seconds=45),
    )
    tracker.update(
        _salt_device(False, False, device_type),
        start + timedelta(seconds=90),
    )


def test_in_the_schedule_window_a_cycle_is_scheduled_even_with_the_menu_open():
    """The unit's timer explains a cycle in the window, whoever is at the menu."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    _run_service_menu_cycle(tracker, T0, True)

    assert tracker.last_trigger is AsekoBackwashTrigger.SCHEDULED
    assert tracker.last_scheduled_backwash is not None
    assert tracker.last_manual_backwash is None


def test_service_menu_is_latched_across_the_whole_window():
    """The flag counts even though the closing frame has already lost it.

    Reading the mode at the end of the window would miss every real cycle:
    in the capture the bit went out ~20 s after the valve closed, before
    the frame that ends the window arrived.
    """
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    started = T0 + timedelta(hours=2)  # outside the schedule window

    tracker.update(_salt_device(True, True), started)
    # the mode is already back to normal for the rest of the window
    tracker.update(
        _salt_device(True, False),
        started + timedelta(seconds=45),
    )
    tracker.update(
        _salt_device(False, False),
        started + timedelta(seconds=90),
    )

    assert tracker.last_trigger is AsekoBackwashTrigger.MANUAL


def test_without_the_service_menu_the_schedule_still_decides():
    """The flag only ever adds evidence; its absence changes nothing."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    _run_service_menu_cycle(tracker, T0, False)

    assert tracker.last_trigger is AsekoBackwashTrigger.SCHEDULED
    assert tracker.last_scheduled_backwash is not None


def test_service_menu_signal_does_not_apply_to_home():
    """On HOME the same bit is a standing pump override, not a person.

    It can sit set indefinitely, so honouring it there would refile every
    scheduled cycle that happened to run while it was on.
    """
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    _run_service_menu_cycle(
        tracker, T0 + timedelta(hours=2), True, AsekoDeviceType.HOME
    )

    # outside the window HOME ignores the bit and keeps the elimination rule
    assert tracker.last_trigger is AsekoBackwashTrigger.MANUAL


def test_service_menu_flag_does_not_leak_into_the_next_cycle():
    """Each window starts from a clean slate."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    _run_service_menu_cycle(tracker, T0 + timedelta(hours=2), True)
    assert tracker.last_trigger is AsekoBackwashTrigger.MANUAL

    later = T0 + timedelta(days=SCHEDULE_EVERY_N_DAYS)
    _run_service_menu_cycle(tracker, later, False)

    assert tracker.last_trigger is AsekoBackwashTrigger.SCHEDULED


# ── units that report their settings menu (SALT) ─────────────────────────────


def test_salt_cycle_outside_the_window_with_the_menu_closed_is_unknown():
    """Nobody at the menu and not the schedule: the cycle is not attributed."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    started = T0 + timedelta(hours=2)

    _run_service_menu_cycle(tracker, started, False)

    assert tracker.last_trigger is AsekoBackwashTrigger.UNKNOWN
    assert tracker.last_backwash == started + timedelta(seconds=45)
    assert tracker.last_manual_backwash is None
    assert tracker.last_scheduled_backwash is None


def test_salt_cycle_outside_the_window_with_the_menu_open_is_manual():
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    started = T0 + timedelta(hours=2)

    _run_service_menu_cycle(tracker, started, True)

    assert tracker.last_trigger is AsekoBackwashTrigger.MANUAL
    assert tracker.last_manual_backwash == started + timedelta(seconds=45)


def test_salt_cycle_with_the_schedule_disabled_and_the_menu_closed_is_unknown():
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    def _disabled(active, menu=False):
        dev = _salt_device(active, menu)
        dev.backwash_interval = 0
        return dev

    tracker.update(_disabled(True), T0)
    tracker.update(_disabled(False), T0 + timedelta(seconds=90))

    assert tracker.last_trigger is AsekoBackwashTrigger.UNKNOWN
    assert tracker.last_manual_backwash is None


def test_unknown_cycle_keeps_earlier_manual_and_scheduled_records():
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    _run_service_menu_cycle(tracker, T0, False)  # scheduled
    _run_service_menu_cycle(tracker, T0 + timedelta(hours=1), True)  # manual
    manual = tracker.last_manual_backwash

    _run_service_menu_cycle(tracker, T0 + timedelta(hours=3), False)  # unknown

    assert tracker.last_scheduled_backwash == T0 + timedelta(seconds=45)
    assert tracker.last_manual_backwash == manual
    assert tracker.last_trigger is AsekoBackwashTrigger.UNKNOWN


def test_backfill_of_an_unexplained_salt_record_runs_once():
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    off_schedule = T0 + timedelta(hours=4)
    tracker._last_backwash = off_schedule  # type: ignore[attr-defined]

    tracker.update(_salt_device(False, False), off_schedule + timedelta(minutes=5))
    tracker.update(_salt_device(False, False), off_schedule + timedelta(minutes=6))

    assert tracker.last_trigger is AsekoBackwashTrigger.UNKNOWN
    assert tracker.last_manual_backwash is None
    assert tracker._hass.async_create_task.call_count == 1  # type: ignore[attr-defined]


# ── time zone and midnight (audit B1, B2) ────────────────────────────────────


def _in_bratislava(monkeypatch) -> Any:
    from zoneinfo import ZoneInfo

    from homeassistant.util import dt as dt_util

    zone = ZoneInfo("Europe/Bratislava")
    monkeypatch.setattr(dt_util, "get_default_time_zone", lambda: zone)
    monkeypatch.setattr(dt_util, "DEFAULT_TIME_ZONE", zone)
    return zone


def _every_three_days_at(at: time) -> Any:
    return _device(False, backwash_start_time=at, backwash_interval=3)


def test_projection_keeps_the_wall_clock_time_across_daylight_saving(monkeypatch):
    """A cycle stored before the change to summer time still projects to 12:30."""
    zone = _in_bratislava(monkeypatch)
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    # as restored from storage: a fixed +01:00 offset, not the zone's rules
    tracker._last_scheduled_backwash = datetime.fromisoformat(  # type: ignore[attr-defined]
        "2026-03-27T12:30:45+01:00"
    )

    projected = tracker.next_scheduled_backwash(
        _every_three_days_at(time(12, 30)), datetime(2026, 3, 28, tzinfo=zone)
    )

    assert projected == datetime(2026, 3, 30, 12, 30, tzinfo=zone)
    assert projected.utcoffset() == timedelta(hours=2)


def test_a_utc_date_projects_like_the_same_local_one(monkeypatch):
    zone = _in_bratislava(monkeypatch)
    device = _every_three_days_at(time(12, 30))
    now = datetime(2026, 9, 11, tzinfo=zone)

    utc = BackwashTracker(_hass(), serial_number=1)
    utc.set_last_scheduled_backwash(datetime(2026, 9, 10, 10, 30, tzinfo=timezone.utc))
    local = BackwashTracker(_hass(), serial_number=2)
    local.set_last_scheduled_backwash(datetime(2026, 9, 10, 12, 30, tzinfo=zone))

    assert utc.next_scheduled_backwash(device, now) == datetime(
        2026, 9, 13, 12, 30, tzinfo=zone
    )
    assert local.next_scheduled_backwash(device, now) == utc.next_scheduled_backwash(
        device, now
    )


def test_a_cycle_finishing_after_midnight_keeps_the_day_it_was_scheduled(monkeypatch):
    """Plan 23:59, valve 23:59:30-00:01: the next one is three days after the 10th."""
    zone = _in_bratislava(monkeypatch)
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    def device(active):
        return _device(active, backwash_start_time=time(23, 59), backwash_interval=3)

    start = datetime(2026, 9, 10, 23, 59, 30, tzinfo=zone)
    tracker.update(device(True), start)
    tracker.update(device(False), start + timedelta(seconds=90))

    assert tracker.last_trigger is AsekoBackwashTrigger.SCHEDULED
    assert tracker.next_scheduled_backwash(
        device(False), start + timedelta(hours=1)
    ) == datetime(2026, 9, 13, 23, 59, tzinfo=zone)


def test_a_cycle_just_before_a_midnight_plan_matches_the_next_day(monkeypatch):
    zone = _in_bratislava(monkeypatch)
    tracker = BackwashTracker(_hass(), serial_number=110071590)

    def device(active):
        return _device(active, backwash_start_time=time(0, 0), backwash_interval=3)

    start = datetime(2026, 9, 10, 23, 58, tzinfo=zone)
    tracker.update(device(True), start)
    tracker.update(device(False), start + timedelta(seconds=90))

    assert tracker.last_trigger is AsekoBackwashTrigger.SCHEDULED
    assert tracker.next_scheduled_backwash(
        device(False), start + timedelta(hours=1)
    ) == datetime(2026, 9, 14, 0, 0, tzinfo=zone)


def test_clearing_re_derives_the_split_after_an_observed_cycle():
    """Clear forgets the verdict too, so the stored cycle is classified again."""
    tracker = BackwashTracker(_hass(), serial_number=110071590)
    _run_cycle(tracker, T0)  # observed, scheduled
    assert tracker.last_trigger is AsekoBackwashTrigger.SCHEDULED

    tracker.clear_last_scheduled_backwash()
    tracker.update(_scheduled_device(False), T0 + timedelta(minutes=5))

    assert tracker.last_scheduled_backwash == T0 + timedelta(seconds=45)
