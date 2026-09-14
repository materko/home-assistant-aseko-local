"""The frame log: a ring buffer of frames and markers with a hard compressed cap."""

from __future__ import annotations

import base64
import random
import zlib
from datetime import UTC, datetime, timedelta

import pytest

from custom_components.aseko_local.recording.frame_log import (
    KIND_MARK,
    KIND_V7,
    KIND_V8,
    FrameLog,
    decode_lines,
)

from .test_decode_v8 import REFERENCE_FRAME

T0 = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


def _v8_frames(count: int, seed: int = 1):
    """Frames of one v8 unit every ten seconds, with the jitter a real one has."""
    rng = random.Random(seed)
    parts = REFERENCE_FRAME.decode().strip().split()
    ins, ains = parts.index("ins:"), parts.index("ains:")
    for i in range(count):
        received = T0 + timedelta(seconds=10 * i + rng.random() * 0.3)
        frame = list(parts)
        frame[ins + 17] = str(received.hour)
        frame[ins + 18] = str(received.minute)
        frame[ains + 1] = frame[ains + 2] = str(708 + rng.choice((-1, 0, 0, 1)))
        frame[ains + 7] = frame[ains + 8] = str(779 + rng.choice((-2, -1, 0, 1, 2)))
        yield received, " ".join(frame).encode()


def test_records_come_back_in_order_with_absolute_times() -> None:
    log = FrameLog()
    frames = list(_v8_frames(100))
    for received, raw in frames[:50]:
        log.append_frame(received, KIND_V8, raw)
    number = log.append_marker(frames[49][0] + timedelta(seconds=3), "heating ON")
    for received, raw in frames[50:]:
        log.append_frame(received, KIND_V8, raw)
    log.append_frame(frames[-1][0], KIND_V7, bytes(range(120)))

    records = log.records()
    assert number == 1
    assert len(records) == 102
    assert records[50] == {
        "k": KIND_MARK,
        "n": 1,
        "note": "heating ON",
        "t": records[50]["t"],
    }
    assert (
        abs(
            datetime.fromisoformat(records[50]["t"]).timestamp()
            - (frames[49][0].timestamp() + 3)
        )
        < 0.06
    )
    assert records[0]["d"] == frames[0][1].decode()
    assert records[-1] == {
        "k": KIND_V7,
        "d": bytes(range(120)).hex(),
        "t": records[-1]["t"],
    }
    times = [datetime.fromisoformat(r["t"]) for r in records]
    assert times == sorted(times)


def test_the_cap_is_never_exceeded_and_old_chunks_go_first() -> None:
    log = FrameLog(max_bytes=32 * 1024, chunk_bytes=4 * 1024)
    for received, raw in _v8_frames(20000):
        log.append_frame(received, KIND_V8, raw)
        assert log.size() <= log.max_bytes
    records = log.records()
    assert log.export()["dropped_chunks"] > 0
    # the newest frame is always kept, the oldest are gone
    assert records[-1]["t"].startswith(
        (T0 + timedelta(seconds=10 * 19999)).isoformat()[:16]
    )
    assert datetime.fromisoformat(records[0]["t"]) > T0 + timedelta(days=1)


def test_rounded_time_deltas_do_not_drift() -> None:
    log = FrameLog()
    frames = list(_v8_frames(5000))
    for received, raw in frames:
        log.append_frame(received, KIND_V8, raw)
    last = datetime.fromisoformat(log.records()[-1]["t"])
    assert abs(last.timestamp() - frames[-1][0].timestamp()) < 0.06


def test_every_chunk_starts_with_an_absolute_time() -> None:
    """Dropping old chunks must never leave a stream that starts with a delta."""
    log = FrameLog(max_bytes=32 * 1024, chunk_bytes=4 * 1024)
    for received, raw in _v8_frames(5000):
        log.append_frame(received, KIND_V8, raw)
    for chunk in log._chunks:  # noqa: SLF001
        first = zlib.decompress(chunk).splitlines()[0]
        assert first.startswith(b'{"t":')


def test_huge_frames_cannot_break_the_ceiling() -> None:
    log = FrameLog(max_bytes=8 * 1024, chunk_bytes=2 * 1024)
    rng = random.Random(7)
    for i in range(300):
        noise = bytes(rng.randrange(256) for _ in range(rng.randrange(1, 3000)))
        log.append_frame(T0 + timedelta(seconds=i), KIND_V7, noise)
        assert log.size() <= log.max_bytes


def test_store_roundtrip_keeps_frames_markers_and_numbering() -> None:
    log = FrameLog(max_bytes=64 * 1024, chunk_bytes=4 * 1024)
    frames = list(_v8_frames(3000))
    for received, raw in frames[:2000]:
        log.append_frame(received, KIND_V8, raw)
    log.append_marker(frames[1999][0], "before restart")

    restored = FrameLog(max_bytes=64 * 1024, chunk_bytes=4 * 1024)
    restored.load_store(log.to_store())
    assert restored.records() == log.records()

    for received, raw in frames[2000:]:
        restored.append_frame(received, KIND_V8, raw)
    assert restored.append_marker(frames[-1][0]) == 2
    assert restored.size() <= restored.max_bytes
    times = [datetime.fromisoformat(r["t"]) for r in restored.records()]
    assert times == sorted(times)


def test_unreadable_store_starts_an_empty_log() -> None:
    log = FrameLog()
    log.load_store({"chunks": ["not base64 zlib"], "open": "???"})
    assert log.records() == []
    log.append_frame(T0, KIND_V7, b"\x00" * 120)
    assert len(log.records()) == 1


def test_export_blob_decodes_to_the_same_records() -> None:
    log = FrameLog(max_bytes=32 * 1024, chunk_bytes=4 * 1024)
    for received, raw in _v8_frames(3000):
        log.append_frame(received, KIND_V8, raw)
    log.append_marker(T0 + timedelta(hours=9), "display photo 1")

    exported = log.export(recent=5)
    blob = zlib.decompress(base64.b64decode(exported["blob"]))
    assert list(decode_lines(blob.splitlines(keepends=True))) == log.records()
    assert exported["records"] == len(log.records())
    assert exported["markers"][0]["note"] == "display photo 1"
    assert len(exported["recent"]) == 5
    assert exported["size_bytes"] <= exported["cap_bytes"]


def test_chunk_size_must_leave_room_under_the_cap() -> None:
    with pytest.raises(ValueError):
        FrameLog(max_bytes=10_000, chunk_bytes=6_000)


def test_coordinator_logs_every_frame_and_numbers_markers() -> None:
    from .test_entity_growth import _coordinator

    coordinator = _coordinator()
    coordinator.store_v8_frame(REFERENCE_FRAME)
    coordinator.store_raw_frame(bytes(120))
    coordinator.store_raw_frame(bytes(40))  # partial frame
    marker = coordinator.mark_dump("photo of the display")

    records = coordinator.frame_log.records()
    assert [r["k"] for r in records] == ["v8", "v7", "partial", "mark"]
    assert marker["marker"] == 1
    assert records[-1]["note"] == "photo of the display"
    assert marker["time"].tzinfo is not None
    # the v8 reference unit and the all-zero v7 serial both reported just now
    assert set(marker["seconds_since_last_frame"]) == {123456789, 0}
    assert all(0 <= age < 5 for age in marker["seconds_since_last_frame"].values())
    assert records[-1]["since"] == {
        str(serial): age for serial, age in marker["seconds_since_last_frame"].items()
    }


@pytest.mark.asyncio
async def test_waiting_for_the_next_frame() -> None:
    import asyncio

    from .test_entity_growth import _coordinator

    coordinator = _coordinator()
    coordinator.hass.loop = asyncio.get_running_loop()

    waiting = asyncio.create_task(coordinator.async_wait_for_frame(5))
    await asyncio.sleep(0)
    assert not waiting.done()
    coordinator.store_v8_frame(REFERENCE_FRAME)
    assert await waiting is True

    assert await coordinator.async_wait_for_frame(0.01) is False
    assert coordinator._frame_waiters == []  # noqa: SLF001


def test_mark_dump_notification_says_whether_the_marker_is_written() -> None:
    from custom_components.aseko_local import _mark_dump_message

    written = {
        "marker": 3,
        "time": "2026-09-13T12:01:05+02:00",
        "seconds_since_last_frame": {110000001: 0.2},
        "waited_for_frame": True,
        "seconds_after_tap": 7.1,
    }
    text = _mark_dump_message([written], wait=True, label=" (heating ON)")
    assert "Marker **3** (heating ON) written at 12:01:05" in text
    assert "7.1 s after the tap" in text
    assert "change the unit again" in text

    timed_out = {**written, "waited_for_frame": False}
    assert "No frame within 60 s" in _mark_dump_message([timed_out], True, "")

    immediate = {**written, "waited_for_frame": None}
    assert "last frame 0.2 s before" in _mark_dump_message([immediate], False, "")


def test_cases_list_survives_restart_and_tracks_downloads() -> None:
    log = FrameLog(max_bytes=32 * 1024, chunk_bytes=4 * 1024)
    frames = list(_v8_frames(200))
    for received, raw in frames[:100]:
        log.append_frame(received, KIND_V8, raw)
    log.append_marker(frames[99][0], "Heating control ON", extra={"photo": "a.jpg"})
    log.append_marker(frames[99][0] + timedelta(seconds=5), "Winter mode ON")

    assert [m["note"] for m in log.markers()] == [
        "Heating control ON",
        "Winter mode ON",
    ]
    assert log.not_downloaded() == 2
    assert all(m["frames"] and not m["downloaded"] for m in log.markers())

    log.mark_exported(1)
    restored = FrameLog(max_bytes=32 * 1024, chunk_bytes=4 * 1024)
    restored.load_store(log.to_store())
    assert [m["downloaded"] for m in restored.markers()] == [True, False]
    assert restored.markers()[0]["photo"] == "a.jpg"
    assert restored.not_downloaded() == 1

    # the frames of old cases age out, the cases stay listed
    for received, raw in _v8_frames(20000, seed=2):
        restored.append_frame(received + timedelta(days=3), KIND_V8, raw)
    assert len(restored.markers()) == 2
    assert not restored.markers()[0]["frames"]

    restored.forget_markers()
    assert restored.markers() == []


def test_an_older_store_gets_its_cases_rebuilt_from_the_frames() -> None:
    log = FrameLog()
    frames = list(_v8_frames(20))
    for received, raw in frames:
        log.append_frame(received, KIND_V8, raw)
    log.append_marker(frames[-1][0], "heating on")
    old_store = log.to_store()
    del old_store["markers"], old_store["exported_through"]

    restored = FrameLog()
    restored.load_store(old_store)
    assert [m["note"] for m in restored.markers()] == ["heating on"]
    assert restored.not_downloaded() == 1


def test_open_chunk_is_sealed_by_uncompressed_size_too() -> None:
    """R10: well-compressing frames must not pile up uncompressed in memory."""
    log = FrameLog()
    frames = list(_v8_frames(43_200))  # five days, one frame every ten seconds
    for received, raw in frames:
        log.append_frame(received, KIND_V8, raw)
    held = sum(len(line) for line in log._current_lines)  # noqa: SLF001
    assert held < log.chunk_raw_bytes + 2_000
    assert log.size() <= log.max_bytes


def test_snapshot_reads_the_same_as_the_log_and_stays_put() -> None:
    """R10: the export works on a copy; frames arriving afterwards do not change it."""
    log = FrameLog()
    frames = list(_v8_frames(3_000))
    for received, raw in frames[:2_000]:
        log.append_frame(received, KIND_V8, raw)
    snapshot = log.snapshot()
    expected = log.records()
    for received, raw in frames[2_000:]:
        log.append_frame(received, KIND_V8, raw)
    assert snapshot.records() == expected
    assert snapshot.export()["records"] == len(expected)


def test_oldest_frame_time_survives_dropping_and_a_restart() -> None:
    """The age of the oldest frame comes from a side list, not a decompression."""
    log = FrameLog(max_bytes=64 * 1024)
    for received, raw in _v8_frames(20_000):
        log.append_frame(received, KIND_V8, raw)
    first = datetime.fromisoformat(log.records()[0]["t"])
    assert log._oldest_time() == first  # noqa: SLF001

    restored = FrameLog(max_bytes=64 * 1024)
    restored.load_store(log.to_store())
    assert restored._oldest_time() == first  # noqa: SLF001


@pytest.mark.parametrize(
    "damage",
    [
        {"next_marker": "broken"},
        {"exported_through": None},
        {"markers": "not a list"},
        {"chunks": ["!!not base64!!"]},
        {"dropped_chunks": [1]},
    ],
)
def test_a_damaged_store_leaves_the_log_empty_instead_of_raising(damage) -> None:
    """A broken diagnostic history must never stop the integration from starting."""
    log = FrameLog()
    for received, raw in _v8_frames(50):
        log.append_frame(received, KIND_V8, raw)
    log.append_marker(T0, "a case")
    stored = {**log.to_store(), **damage}

    restored = FrameLog()
    restored.load_store(stored)  # must not raise
    assert restored.records() == []
    assert restored.markers() == []


@pytest.mark.asyncio
async def test_a_fragment_or_another_unit_does_not_end_the_wait() -> None:
    """R8: only a whole frame from the unit being waited for writes the marker."""
    import asyncio

    from .test_entity_growth import _coordinator

    coordinator = _coordinator()
    coordinator.hass.loop = asyncio.get_running_loop()

    waiting = asyncio.create_task(
        coordinator.async_wait_for_frame(5, serial_number=123456789)
    )
    await asyncio.sleep(0)
    coordinator.store_raw_frame(b"\x00\x00\x04\xd2")  # four bytes, no measurements
    other = bytearray(120)
    other[0:4] = (1234).to_bytes(4, "big")
    coordinator.store_raw_frame(bytes(other))  # a whole frame, another unit
    await asyncio.sleep(0)
    assert not waiting.done()

    coordinator.store_v8_frame(REFERENCE_FRAME)  # serial 123456789
    assert await waiting is True
    assert coordinator._frame_waiters == []  # noqa: SLF001


def test_rejected_bytes_are_logged_with_their_reason_and_counted() -> None:
    from .test_entity_growth import _coordinator

    coordinator = _coordinator()
    coordinator.store_rejected_frame(bytes(range(120)), "frame sync failed: IndexError")
    coordinator.store_rejected_frame(bytes(range(120)), "frame sync failed: IndexError")

    records = coordinator.frame_log.records()
    assert [r["k"] for r in records] == ["rejected", "rejected"]
    assert records[0]["why"] == "frame sync failed: IndexError"
    assert records[0]["d"] == bytes(range(120)).hex()
    assert (
        coordinator.get_rejected_frames()["frame sync failed: IndexError"]["count"] == 2
    )
