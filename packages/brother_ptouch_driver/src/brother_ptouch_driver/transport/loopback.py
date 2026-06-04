"""In-memory loopback transport for hardware-free testing.

Records everything written and replays canned reply bytes (e.g. a status
reply). Implements the Transport protocol so it is a drop-in for
``UsbTransport`` in tests and future integration suites. See issue #9.
"""

from __future__ import annotations

from collections.abc import Iterable

from brother_ptouch_driver.transport.errors import TransportTimeoutError


class LoopbackTransport:
    """In-memory Transport that records writes and replays canned replies."""

    def __init__(self, replies: Iterable[bytes] = ()) -> None:
        self.written = bytearray()
        self._reads = bytearray()
        for reply in replies:
            self._reads.extend(reply)
        self.opened = False
        self.close_count = 0

    def queue_reply(self, data: bytes) -> None:
        """Append bytes the printer should return on subsequent reads."""
        self._reads.extend(data)

    def open(self) -> None:
        """Mark the transport open."""
        self.opened = True

    def close(self) -> None:
        """Mark the transport closed, counting transitions from open."""
        if self.opened:
            self.close_count += 1
        self.opened = False

    def __enter__(self) -> LoopbackTransport:
        self.open()
        return self

    def __exit__(self, *_exc_info: object) -> bool:
        self.close()
        return False

    def write(self, data: bytes) -> int:
        """Record bytes and report how many were written."""
        self.written.extend(data)
        return len(data)

    def read(self, n: int, timeout_ms: int | None = None) -> bytes:
        """Return up to n queued bytes, consuming what is returned."""
        chunk = bytes(self._reads[:n])
        del self._reads[:n]
        return chunk

    def read_exact(self, n: int, timeout_ms: int | None = None) -> bytes:
        """Return exactly n queued bytes or raise if too few are queued."""
        if len(self._reads) < n:
            msg = f"loopback has {len(self._reads)} bytes queued, need {n}"
            raise TransportTimeoutError(msg)
        chunk = bytes(self._reads[:n])
        del self._reads[:n]
        return chunk
