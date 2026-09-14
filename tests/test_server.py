import asyncio

import pytest

from custom_components.aseko_local.models import AsekoDevice
from custom_components.aseko_local.server import (
    AsekoDeviceServer,
    FrameType,
)


# Hilfsfunktion: Hex-String zu Bytes
def hexstr_to_bytes(s: str) -> bytes:
    return bytes.fromhex(s.replace("\n", "").replace(" ", ""))


# Reales gültiges Frame (gekürzt für Beispiel)
VALID_FRAME_HEX = (
    "069187240901ffffffffffff000402da0027ffff0095ff01400149ff000006640000000000ff006c"
    "069187240903ffffffffffff480a08ffffffffffffffffff027e0149ffffffffffffffffffffffea"
    "069187240902ffffffffffff0001003cffff003cffff010383ff00781e02581e28ffffffff0049a9"
)
VALID_FRAME2_HEX = (
    "069187250901ffffffffffff000402da0027ffff0095ff01400149ff000006640000000000ff006c"
    "069187250903ffffffffffff480a08ffffffffffffffffff027e0149ffffffffffffffffffffffea"
    "069187250902ffffffffffff0001003cffff003cffff010383ff00781e02581e28ffffffff0049a9"
)
VALID_FRAME = hexstr_to_bytes(VALID_FRAME_HEX)  # MESSAGE_SIZE = 120
VALID_FRAME2 = hexstr_to_bytes(VALID_FRAME2_HEX)  # MESSAGE_SIZE = 120

# Korruptes Frame: pH Wert ungültig (z.B. 99.99)
CORRUPT_FRAME = bytearray(VALID_FRAME)
CORRUPT_FRAME[14:16] = (9999).to_bytes(2, "big")  # pH = 99.99


class DummyWriter:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.closed = False

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        pass

    def get_extra_info(self, name: str):
        # Simuliere Peername für Tests
        if name == "peername":
            return (self.host, self.port)
        return None


class DummyServer:
    def is_serving(self) -> bool:
        return True

    def close(self) -> None:
        pass

    async def wait_closed(self) -> None:
        pass


@pytest.mark.asyncio
async def test_valid_device_frame(monkeypatch) -> None:
    """Test: Bestehendes Device wird erkannt und verarbeitet."""

    called = {}

    async def on_data(device: AsekoDevice) -> None:
        called["serial"] = device.serial_number

    async def dummy_start_server(handler, host, port) -> DummyServer:
        # Simulate a connection with valid data
        reader = asyncio.StreamReader()
        writer = DummyWriter("127.0.0.1", 12344)
        reader.feed_data(VALID_FRAME)
        reader.feed_eof()
        await handler(reader, writer)
        return DummyServer()

    monkeypatch.setattr(asyncio, "start_server", dummy_start_server)

    server = await AsekoDeviceServer.create(
        host="127.0.0.1", port=12344, on_data=on_data
    )
    assert server.running
    # Serial number should be captured
    assert "serial" in called
    assert called["serial"] == 110200612
    await server.stop()


@pytest.mark.asyncio
async def test_multiple_valid_device_frames(monkeypatch) -> None:
    """Test: Multiple valid device frames are processed correctly."""

    called = []

    async def on_data(device: AsekoDevice) -> None:
        called.append(device)

    async def dummy_start_server(handler, host, port) -> DummyServer:
        # Simulate a connection with valid data
        writer = DummyWriter("127.0.0.1", 12345)

        reader = asyncio.StreamReader()
        reader.feed_data(VALID_FRAME)
        reader.feed_eof()
        await handler(reader, writer)

        reader = asyncio.StreamReader()
        reader.feed_data(VALID_FRAME2)
        reader.feed_eof()
        await handler(reader, writer)

        return DummyServer()

    monkeypatch.setattr(asyncio, "start_server", dummy_start_server)

    server = await AsekoDeviceServer.create(
        host="127.0.0.1", port=12345, on_data=on_data
    )
    assert server.running
    # 2 serial numbers should be captured
    assert len(called) == 2
    assert called[0].serial_number == 110200612
    assert called[1].serial_number == 110200613
    await server.stop()


@pytest.mark.asyncio
async def test_implausible_frame_is_decoded_and_reported(monkeypatch) -> None:
    """An implausible pH no longer closes the connection.

    The frame is still decoded and handed on -- a unit nobody has mapped may
    lay its bytes out differently -- the reason goes to the warning sink for
    diagnostics, and the next frame on the same connection is read too.
    """

    devices: list[AsekoDevice] = []
    warnings: list[tuple[int, str]] = []

    async def on_data(device: AsekoDevice) -> None:
        devices.append(device)

    def frame_warning_sink(serial: int, reason: str) -> None:
        warnings.append((serial, reason))

    async def dummy_start_server(handler, host, port) -> DummyServer:
        reader = asyncio.StreamReader()
        writer = DummyWriter("127.0.0.1", 12346)
        reader.feed_data(bytes(CORRUPT_FRAME) + VALID_FRAME2)
        reader.feed_eof()
        await handler(reader, writer)
        return DummyServer()

    monkeypatch.setattr(asyncio, "start_server", dummy_start_server)

    server = await AsekoDeviceServer.create(
        host="127.0.0.1",
        port=12346,
        on_data=on_data,
        frame_warning_sink=frame_warning_sink,
    )
    assert server.running
    assert [d.serial_number for d in devices] == [110200612, 110200613]
    assert warnings == [(110200612, "pH 99.99 outside 0-14")]
    await server.stop()


@pytest.mark.asyncio
async def test_issue_61_shifted_frame(monkeypatch) -> None:
    """Test: Shifted frame from issue 61."""

    BYTE_FRAME = hexstr_to_bytes(
        "0f0f1e14ffbf02970690cafe0301190a12103232000402cb015201520152a3fe700099fe00080000"
        "00000000001302670690cafe0303190a121032324842011d080f122d15001737027600a9000c1e0a"
        "012801e00e10a2020690cafe0302190a12103232002d003c003c003c000a1e3c6e9600f00802580f"
    )

    called = {}

    async def on_data(device: AsekoDevice) -> None:
        called["serial"] = device.serial_number

    async def dummy_start_server(handler, host, port) -> DummyServer:
        # Simulate a connection with valid data
        reader = asyncio.StreamReader()
        writer = DummyWriter("127.0.0.1", 12347)
        reader.feed_data(BYTE_FRAME)
        reader.feed_eof()
        await handler(reader, writer)
        return DummyServer()

    monkeypatch.setattr(asyncio, "start_server", dummy_start_server)

    server = await AsekoDeviceServer.create(
        host="127.0.0.1", port=12347, on_data=on_data
    )
    assert server.running
    # Serial number should be captured
    assert "serial" in called
    assert called["serial"] == 110152446
    await server.stop()


# ---------------------------------------------------------------------------
# v8 frame tests
# ---------------------------------------------------------------------------

# Minimal synthetic v8 frame: starts with '{v1 ', ends with '}'
V8_INITIAL = b"{v1 12345678" + b" " * 108  # 120 bytes, starts with '{v1 '
assert len(V8_INITIAL) == 120
V8_REST = (
    b" ins: 0000 outs: 0000 crc16: ABCD}\n"  # read by readuntil(b'\n'), includes \n
)
V8_FULL_FRAME = V8_INITIAL + V8_REST  # exact bytes the device sends

# Shifted v8 frame: 3 garbage prefix bytes before the '{v1 ' signature
V8_SHIFTED_PREFIX = b"\x00\x00\x00"
V8_SHIFTED_INITIAL = V8_SHIFTED_PREFIX + b"{v1 12345678" + b" " * 105  # 120 bytes
assert len(V8_SHIFTED_INITIAL) == 120
V8_SHIFTED_FULL_FRAME = V8_SHIFTED_INITIAL[3:] + V8_REST  # starts at '{', exact bytes


@pytest.mark.asyncio
async def test_v8_frame_forwarded_before_decode() -> None:
    """v8 frames must be forwarded even if the frame body is unparseable."""

    v8_forwarded = {}

    async def v8_forward_cb(frame: bytes) -> None:
        v8_forwarded["frame"] = frame

    server = AsekoDeviceServer(host="127.0.0.1", port=12350, on_data=None)
    server.set_forward_v8_callback(v8_forward_cb)

    reader = asyncio.StreamReader()
    writer = DummyWriter("127.0.0.1", 12350)
    reader.feed_data(V8_FULL_FRAME)
    reader.feed_eof()
    await server._handle_client(reader, writer)

    # forward callback must have received the full frame
    assert "frame" in v8_forwarded
    assert v8_forwarded["frame"] == V8_FULL_FRAME


# Real parseable v8 frame — same as REFERENCE_FRAME in test_decode_v8.py
_V8_REAL_FRAME = (
    b"{v1 123456789 804 0 27 "
    b"ins: 314 -500 -500 -500 0 0 0 0 1 -500 -500 -500 0 24 6 29 22 27 0 "
    b"ains: 708 708 774 7790 0 0 779 779 0 0 0 0 0 0 0 0 "
    b"outs: 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"areqs: 74 73 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
    b"reqs: 0 0 0 0 0 0 0 24 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"0 10 10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"fncs: 0 0 3 0 0 0 2 0 "
    b"mods: 2 0 0 1 0 0 0 0 "
    b"flags: 2 0 0 0 0 0 0 0 "
    b"crc16: C3C8}\n"
)
# Split at the 120-byte mark for _sync_frame
_V8_REAL_INITIAL = _V8_REAL_FRAME[:120]
_V8_REAL_REST = _V8_REAL_FRAME[120:]


@pytest.mark.asyncio
async def test_v8_frame_decoded_and_delivered() -> None:
    """A valid v8 frame must be decoded and delivered to on_data."""

    received = {}

    async def on_data(device: AsekoDevice) -> None:
        received["device"] = device

    server = AsekoDeviceServer(host="127.0.0.1", port=12350, on_data=on_data)

    reader = asyncio.StreamReader()
    writer = DummyWriter("127.0.0.1", 12350)
    reader.feed_data(_V8_REAL_FRAME)
    reader.feed_eof()
    await server._handle_client(reader, writer)

    assert "device" in received
    assert received["device"].serial_number == 123456789


@pytest.mark.asyncio
async def test_sync_frame_binary_returns_binary_type() -> None:
    """_sync_frame must return FrameType.BINARY for a non-v8 initial chunk."""

    server = AsekoDeviceServer.__new__(AsekoDeviceServer)

    reader = asyncio.StreamReader()
    frame, offset, frame_type = await server._sync_frame(reader, VALID_FRAME)
    assert frame_type == FrameType.BINARY
    assert offset == 0
    assert frame == VALID_FRAME


@pytest.mark.asyncio
async def test_sync_frame_v8_returns_v8_type() -> None:
    """_sync_frame must return FrameType.V8 when initial chunk starts with '{'."""

    server = AsekoDeviceServer.__new__(AsekoDeviceServer)

    reader = asyncio.StreamReader()
    reader.feed_data(V8_REST)
    reader.feed_eof()

    full, offset, frame_type = await server._sync_frame(reader, V8_INITIAL)
    assert frame_type == FrameType.V8
    assert offset == 0
    assert full == V8_FULL_FRAME


@pytest.mark.asyncio
async def test_sync_frame_v8_shifted() -> None:
    """_sync_frame must find '{v1 ' past a garbage prefix and return correct offset."""

    server = AsekoDeviceServer.__new__(AsekoDeviceServer)

    reader = asyncio.StreamReader()
    reader.feed_data(V8_REST)
    reader.feed_eof()

    full, offset, frame_type = await server._sync_frame(reader, V8_SHIFTED_INITIAL)
    assert frame_type == FrameType.V8
    assert offset == len(V8_SHIFTED_PREFIX)  # 3
    assert full == V8_SHIFTED_FULL_FRAME


@pytest.mark.asyncio
async def test_sync_frame_binary_shifted() -> None:
    """_sync_frame must rewind a shifted binary frame via _rewind_binary."""

    # This is the issue-61 frame: 8 bytes of a previous frame's tail precede
    # the actual aligned frame content.
    SHIFTED_BINARY = hexstr_to_bytes(
        "0f0f1e14ffbf02970690cafe0301190a12103232000402cb015201520152a3fe700099fe00080000"
        "00000000001302670690cafe0303190a121032324842011d080f122d15001737027600a9000c1e0a"
        "012801e00e10a2020690cafe0302190a12103232002d003c003c003c000a1e3c6e9600f00802580f"
    )

    server = AsekoDeviceServer.__new__(AsekoDeviceServer)
    reader = asyncio.StreamReader()

    frame, offset, frame_type = await server._sync_frame(reader, SHIFTED_BINARY)

    assert frame_type == FrameType.BINARY
    assert offset == 8
    # After rewind, alignment markers must be at the correct positions
    assert frame[5] == 0x01
    assert frame[45] == 0x03
    assert frame[85] == 0x02
    # Serial number must be consistent across all three sub-frames
    assert frame[0:4] == frame[40:44] == frame[80:84]


@pytest.mark.asyncio
async def test_create_restarts_a_server_stopped_but_still_registered(
    monkeypatch,
) -> None:
    """R1: stop() without remove() must not hand a dead server to the next setup."""
    starts = []

    async def dummy_start_server(handler, host, port) -> DummyServer:
        starts.append(port)
        return DummyServer()

    monkeypatch.setattr(asyncio, "start_server", dummy_start_server)
    await AsekoDeviceServer.remove(host="127.0.0.1", port=12350)

    first = await AsekoDeviceServer.create(host="127.0.0.1", port=12350)
    await first.stop()
    assert not first.running

    again = await AsekoDeviceServer.create(host="127.0.0.1", port=12350)
    assert again is first
    assert again.running
    assert starts == [12350, 12350]

    await AsekoDeviceServer.remove(host="127.0.0.1", port=12350)
    assert AsekoDeviceServer.get("127.0.0.1", 12350) is None


@pytest.mark.asyncio
async def test_remove_leaves_other_servers_running(monkeypatch) -> None:
    """R1: stopping one entry's server keeps the others listening."""

    async def dummy_start_server(handler, host, port) -> DummyServer:
        return DummyServer()

    monkeypatch.setattr(asyncio, "start_server", dummy_start_server)
    one = await AsekoDeviceServer.create(host="127.0.0.1", port=12351)
    two = await AsekoDeviceServer.create(host="127.0.0.1", port=12352)

    await AsekoDeviceServer.remove(host="127.0.0.1", port=12351)
    assert not one.running
    assert two.running
    await AsekoDeviceServer.remove(host="127.0.0.1", port=12352)


@pytest.mark.asyncio
async def test_rejected_v8_frame_still_reaches_the_frame_log() -> None:
    """R5: the raw sink sees a v8 frame before the decoder can reject it."""
    logged: list[bytes] = []
    warnings: list[tuple[int, str]] = []

    server = AsekoDeviceServer(
        host="127.0.0.1",
        port=12353,
        on_data=None,
        v8_raw_sink=logged.append,
        frame_warning_sink=lambda serial, reason: warnings.append((serial, reason)),
    )
    reader = asyncio.StreamReader()
    writer = DummyWriter("127.0.0.1", 12353)
    reader.feed_data(V8_FULL_FRAME)  # header without the four numbers: rejected
    reader.feed_eof()
    await server._handle_client(reader, writer)

    assert logged == [V8_FULL_FRAME]
    assert len(warnings) == 1
    assert warnings[0][0] == 12345678
    assert warnings[0][1].startswith("v8 frame rejected:")


@pytest.mark.asyncio
async def test_bytes_that_never_align_are_kept_with_the_reason() -> None:
    """R5: a frame sync failure no longer drops the bytes silently."""
    rejected: list[tuple[bytes, str]] = []
    server = AsekoDeviceServer(
        host="127.0.0.1",
        port=12354,
        on_data=None,
        rejected_sink=lambda data, reason: rejected.append((data, reason)),
    )
    garbage = bytes(range(120))  # no segment markers anywhere: cannot be aligned
    reader = asyncio.StreamReader()
    writer = DummyWriter("127.0.0.1", 12354)
    reader.feed_data(garbage)
    reader.feed_eof()
    await server._handle_client(reader, writer)

    assert len(rejected) == 1
    assert rejected[0][0] == garbage
    assert rejected[0][1].startswith("frame sync failed:")
