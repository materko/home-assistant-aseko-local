import asyncio

import pytest

from custom_components.aseko_local.forwarder import AsekoCloudMirror


class DummyWriter:
    def __init__(self) -> None:
        self.data = []
        self.closed = False

    def write(self, frame: bytes) -> None:
        self.data.append(frame)

    async def drain(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        pass


@pytest.mark.asyncio
async def test_forwarding(monkeypatch) -> None:
    """Test that frames are forwarded by the mirror worker."""

    dummy_writer = DummyWriter()

    async def dummy_open_connection(host: str, port: int) -> tuple[None, DummyWriter]:
        return None, dummy_writer

    monkeypatch.setattr(asyncio, "open_connection", dummy_open_connection)

    mirror = AsekoCloudMirror("localhost", 12345)
    await mirror.start()
    frame = b"\xaa" * 120
    await mirror.enqueue(frame)
    await asyncio.sleep(0.2)  # Give worker time to process
    await mirror.stop()

    # Check that the frame was written to DummyWriter
    assert any(f == frame for f in dummy_writer.data)


@pytest.mark.asyncio
async def test_no_connection_before_first_frame(monkeypatch) -> None:
    """Worker must not open a connection until the first frame is enqueued."""

    connect_count = 0

    async def dummy_open_connection(host: str, port: int) -> tuple[None, DummyWriter]:
        nonlocal connect_count
        connect_count += 1
        return None, DummyWriter()

    monkeypatch.setattr(asyncio, "open_connection", dummy_open_connection)

    mirror = AsekoCloudMirror("localhost", 12345)
    await mirror.start()
    # Give the worker task a chance to run without any frame
    await asyncio.sleep(0.1)

    assert connect_count == 0, "Connection opened before any frame was enqueued"

    await mirror.stop()


@pytest.mark.asyncio
async def test_connect_on_first_frame(monkeypatch) -> None:
    """Worker must open exactly one connection when the first frame arrives."""

    connect_count = 0
    dummy_writer = DummyWriter()

    async def dummy_open_connection(host: str, port: int) -> tuple[None, DummyWriter]:
        nonlocal connect_count
        connect_count += 1
        return None, dummy_writer

    monkeypatch.setattr(asyncio, "open_connection", dummy_open_connection)

    mirror = AsekoCloudMirror("localhost", 12345)
    await mirror.start()
    await asyncio.sleep(0.05)  # worker is blocked in queue.get()
    assert connect_count == 0

    await mirror.enqueue(b"\xbb" * 120)
    await asyncio.sleep(0.1)  # worker processes the frame

    assert connect_count == 1, "Expected exactly one connection after first frame"
    assert len(dummy_writer.data) == 1

    await mirror.stop()


@pytest.mark.asyncio
async def test_multiple_frames_reuse_connection(monkeypatch) -> None:
    """Multiple frames must reuse the same connection — no reconnect per frame."""

    connect_count = 0
    dummy_writer = DummyWriter()

    async def dummy_open_connection(host: str, port: int) -> tuple[None, DummyWriter]:
        nonlocal connect_count
        connect_count += 1
        return None, dummy_writer

    monkeypatch.setattr(asyncio, "open_connection", dummy_open_connection)

    mirror = AsekoCloudMirror("localhost", 12345)
    await mirror.start()

    for i in range(5):
        await mirror.enqueue(bytes([i]) * 120)

    await asyncio.sleep(0.2)  # Give worker time to drain the queue

    assert connect_count == 1, f"Expected 1 connection, got {connect_count}"
    assert len(dummy_writer.data) == 5

    await mirror.stop()


@pytest.mark.asyncio
async def test_a_frame_that_failed_goes_out_before_newer_ones(monkeypatch) -> None:
    """Audit A4: connect fails for A while B waits; the cloud still gets A, B."""
    writer = DummyWriter()
    attempts = {"n": 0}

    async def flaky_open_connection(host: str, port: int):
        attempts["n"] += 1
        if attempts["n"] == 1:
            msg = "cloud unreachable"
            raise OSError(msg)
        return None, writer

    monkeypatch.setattr(asyncio, "open_connection", flaky_open_connection)
    mirror = AsekoCloudMirror("localhost", 12345)
    await mirror.start()
    await mirror.enqueue(b"A")
    await mirror.enqueue(b"B")
    for _ in range(300):
        if len(writer.data) == 2:
            break
        await asyncio.sleep(0.01)
    await mirror.stop()

    assert writer.data == [b"A", b"B"]


@pytest.mark.asyncio
async def test_a_frame_whose_write_failed_goes_out_first(monkeypatch) -> None:
    class FailOnce(DummyWriter):
        def __init__(self) -> None:
            super().__init__()
            self.failed = False

        def write(self, frame: bytes) -> None:
            if not self.failed:
                self.failed = True
                msg = "broken pipe"
                raise OSError(msg)
            super().write(frame)

    writer = FailOnce()

    async def open_connection(host: str, port: int):
        return None, writer

    monkeypatch.setattr(asyncio, "open_connection", open_connection)
    mirror = AsekoCloudMirror("localhost", 12345)
    await mirror.start()
    await mirror.enqueue(b"A")
    await mirror.enqueue(b"B")
    for _ in range(300):
        if len(writer.data) == 2:
            break
        await asyncio.sleep(0.01)
    await mirror.stop()

    assert writer.data == [b"A", b"B"]


@pytest.mark.asyncio
async def test_repeated_write_failures_back_off(monkeypatch) -> None:
    """Audit B3: a cloud that keeps failing writes is not retried in a tight loop."""
    attempts = {"n": 0}

    class AlwaysFails(DummyWriter):
        def write(self, frame: bytes) -> None:
            attempts["n"] += 1
            msg = "broken pipe"
            raise OSError(msg)

    async def open_connection(host: str, port: int):
        return None, AlwaysFails()

    monkeypatch.setattr(asyncio, "open_connection", open_connection)
    mirror = AsekoCloudMirror("localhost", 12345)
    await mirror.start()
    await mirror.enqueue(b"A")
    await asyncio.sleep(0.3)
    await mirror.stop()

    # the first attempt fails, then the worker waits a second before the next
    assert attempts["n"] == 1
