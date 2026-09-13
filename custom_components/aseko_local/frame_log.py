"""A ring buffer of raw frames and user markers, capped in compressed bytes.

Every frame the server receives (v7 binary, v8 text, partial) is appended as
one JSON line with the Home Assistant receive time.  A marker written by the
``mark_dump`` service goes into the same stream, so frames and the photos a
user takes of the unit's display right after tapping the button line up by
position, without anyone comparing clocks.  Photos stay outside, attached to
the GitHub issue by hand.

The ceiling is hard: the sealed compressed chunks, plus the compressed bytes
of the chunk being written, plus the records not yet handed to its
compressor (counted uncompressed) never exceed ``max_bytes``, whatever the
units send.  When the next record would pass it, whole chunks are dropped
from the old end.

Consecutive frames of a unit differ in a few digits, so they compress well
once the receive time stops being the noisiest field: the first record of
each chunk carries the absolute time (``t``) and every later one only the
seconds since the previous record (``dt``).  With that, 256 kB holds about
five days of one v8 unit sending every ten seconds.

The buffer is kept in a Home Assistant ``Store`` so it survives a restart,
and the diagnostics download carries it as one base64 zlib blob -- decode it
with ``scripts/frame_log_tool.py`` -- plus the markers and the latest records
in plain text.
"""

from __future__ import annotations

import base64
import json
import logging
import zlib
from collections import deque
from collections.abc import Iterable, Iterator
from datetime import datetime
from typing import Any

_LOGGER = logging.getLogger(__name__)

DEFAULT_MAX_BYTES = 256 * 1024
DEFAULT_CHUNK_BYTES = 16 * 1024
# Records reach the compressor in batches: a sync flush after every record
# would cost a few bytes each, and a batch this small keeps the uncompressed
# remainder, which counts against the cap at full size, small.
FLUSH_EVERY = 32

KIND_V7 = "v7"
KIND_V8 = "v8"
KIND_PARTIAL = "partial"
KIND_MARK = "mark"


def decode_lines(lines: Iterable[bytes]) -> Iterator[dict[str, Any]]:
    """Turn stored JSON lines back into records with an absolute ``t``.

    A line with ``t`` restarts the clock (every chunk begins with one); a
    line with ``dt`` is that many seconds after the previous record.
    """
    last: datetime | None = None
    for line in lines:
        if not line.strip():
            continue
        record = json.loads(line)
        if "t" in record:
            last = datetime.fromisoformat(record["t"])
        elif last is not None:
            last = datetime.fromtimestamp(
                last.timestamp() + record.pop("dt"), last.tzinfo
            )
            record["t"] = last.isoformat()
        yield record


class FrameLog:
    """Append-only stream of frames and markers with a hard compressed-size cap."""

    def __init__(
        self,
        max_bytes: int = DEFAULT_MAX_BYTES,
        chunk_bytes: int = DEFAULT_CHUNK_BYTES,
    ) -> None:
        if chunk_bytes * 2 > max_bytes:
            raise ValueError("chunk_bytes must be at most half of max_bytes")
        self.max_bytes = max_bytes
        self.chunk_bytes = chunk_bytes
        self._chunks: deque[bytes] = deque()  # sealed zlib streams, oldest first
        self._sealed_bytes = 0
        self._dropped_chunks = 0
        self._next_marker = 1
        self._start_chunk()

    # -- writing -----------------------------------------------------------

    def _start_chunk(self) -> None:
        self._compressor = zlib.compressobj(9)
        self._current = bytearray()  # compressed bytes of the open chunk so far
        self._current_lines: list[bytes] = []  # every record of the open chunk
        self._pending: list[bytes] = []  # records not yet given to the compressor
        self._last_time: datetime | None = None  # None: next record carries ``t``

    def append_frame(self, received: datetime, kind: str, raw: bytes) -> None:
        """Record one frame as it arrived from a unit."""
        if kind == KIND_V8:
            data = raw.decode("ascii", errors="replace").strip()
        else:
            data = bytes(raw).hex()
        self._append(received, {"k": kind, "d": data})

    def append_marker(
        self,
        received: datetime,
        note: str | None = None,
        since_last_frame: dict[str, float] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> int:
        """Record a marker and return its number, counted since the log began.

        ``since_last_frame`` maps a unit's serial number to how many seconds
        before the marker its last frame arrived; ``extra`` adds fields such
        as the name of a display photo uploaded with the marker.
        """
        number = self._next_marker
        self._next_marker += 1
        record: dict[str, Any] = {"k": KIND_MARK, "n": number}
        if note:
            record["note"] = note
        if since_last_frame:
            record["since"] = since_last_frame
        if extra:
            record.update({key: value for key, value in extra.items() if value})
        self._append(received, record)
        return number

    def _append(self, received: datetime, body: dict[str, Any]) -> None:
        if self._last_time is None:
            record = {"t": received.isoformat(), **body}
            self._last_time = received
        else:
            # Measure from the time the reader will reconstruct, not the true
            # previous one, so rounding never accumulates along a chunk.
            delta = round(received.timestamp() - self._last_time.timestamp(), 1)
            record = {"dt": delta, **body}
            self._last_time = datetime.fromtimestamp(
                self._last_time.timestamp() + delta, self._last_time.tzinfo
            )
        self._add_line(json.dumps(record, separators=(",", ":")).encode() + b"\n")

    def _add_line(self, line: bytes) -> None:
        self._current_lines.append(line)
        self._pending.append(line)
        if len(self._pending) >= FLUSH_EVERY:
            self._flush_pending()
        if len(self._current) >= self.chunk_bytes:
            self._seal()
        self._enforce_cap()

    def _flush_pending(self) -> None:
        if not self._pending:
            return
        self._current += self._compressor.compress(b"".join(self._pending))
        self._current += self._compressor.flush(zlib.Z_SYNC_FLUSH)
        self._pending = []

    def _seal(self) -> None:
        self._flush_pending()
        self._current += self._compressor.flush(zlib.Z_FINISH)
        self._chunks.append(bytes(self._current))
        self._sealed_bytes += len(self._current)
        self._start_chunk()

    def size(self) -> int:
        """Upper bound of the compressed size, the figure the cap applies to."""
        pending = sum(len(line) for line in self._pending)
        return self._sealed_bytes + len(self._current) + pending

    def _enforce_cap(self) -> None:
        while self.size() > self.max_bytes and self._chunks:
            self._sealed_bytes -= len(self._chunks.popleft())
            self._dropped_chunks += 1
        if self.size() > self.max_bytes:
            # Only the open chunk is left and it alone passes the cap -- not
            # reachable while chunk_bytes <= max_bytes / 2 and records are
            # small, but the ceiling holds even then.
            self._dropped_chunks += 1
            self._start_chunk()

    def marker_count(self) -> int:
        """How many markers have been written since the log began."""
        return self._next_marker - 1

    # -- reading -----------------------------------------------------------

    def _stored_lines(self) -> Iterator[bytes]:
        for chunk in self._chunks:
            yield from zlib.decompress(chunk).splitlines(keepends=True)
        yield from self._current_lines

    def records(self) -> list[dict[str, Any]]:
        """Every record still held, oldest first, with absolute times."""
        return list(decode_lines(self._stored_lines()))

    def export(self, recent: int = 20) -> dict[str, Any]:
        """The buffer for the diagnostics download."""
        records = self.records()
        return {
            "about": (
                "Raw frames and mark_dump markers in the order Home Assistant "
                "received them. 'blob' is the whole buffer: base64 of zlib-compressed "
                "JSON lines; decode it with scripts/frame_log_tool.py."
            ),
            "cap_bytes": self.max_bytes,
            "size_bytes": self.size(),
            "records": len(records),
            "oldest": records[0]["t"] if records else None,
            "newest": records[-1]["t"] if records else None,
            "dropped_chunks": self._dropped_chunks,
            "markers": [r for r in records if r.get("k") == KIND_MARK],
            "recent": records[-recent:],
            "blob": base64.b64encode(
                zlib.compress(b"".join(self._stored_lines()), 9)
            ).decode(),
        }

    # -- persistence -------------------------------------------------------

    def to_store(self) -> dict[str, Any]:
        """Serialisable state: sealed chunks as they are, the open chunk recompressed."""
        return {
            "chunks": [base64.b64encode(chunk).decode() for chunk in self._chunks],
            "open": base64.b64encode(
                zlib.compress(b"".join(self._current_lines), 9)
            ).decode(),
            "dropped_chunks": self._dropped_chunks,
            "next_marker": self._next_marker,
        }

    def load_store(self, data: dict[str, Any]) -> None:
        """Restore what ``to_store`` saved; an unreadable store leaves the log empty."""
        try:
            chunks = [base64.b64decode(chunk) for chunk in data.get("chunks", [])]
            for chunk in chunks:
                zlib.decompress(chunk)
            stored_open = data.get("open")
            open_lines = (
                zlib.decompress(base64.b64decode(stored_open)) if stored_open else b""
            )
            open_records = list(decode_lines(open_lines.splitlines(keepends=True)))
        except (ValueError, TypeError, KeyError, zlib.error) as err:
            _LOGGER.warning("Discarding an unreadable Aseko frame log: %s", err)
            return
        self._chunks = deque(chunks)
        self._sealed_bytes = sum(len(chunk) for chunk in chunks)
        self._dropped_chunks = int(data.get("dropped_chunks", 0))
        self._next_marker = int(data.get("next_marker", 1))
        self._start_chunk()
        # Re-encode rather than replay the lines: a chunk sealed on the way
        # must start again with an absolute time.
        for record in open_records:
            received = datetime.fromisoformat(record.pop("t"))
            self._append(received, record)
        self._enforce_cap()
