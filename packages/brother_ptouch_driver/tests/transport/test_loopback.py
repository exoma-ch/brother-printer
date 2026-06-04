"""Tests for the in-memory LoopbackTransport (issue #9)."""

from __future__ import annotations

import pytest

from brother_ptouch_driver.transport import LoopbackTransport, Transport
from brother_ptouch_driver.transport.errors import TransportTimeoutError


def test_loopback_conforms_to_transport_protocol():
    """LoopbackTransport satisfies the runtime-checkable Transport protocol."""
    assert isinstance(LoopbackTransport(), Transport)


def test_write_records_bytes_and_returns_length():
    """write() appends to the captured buffer and reports bytes written."""
    transport = LoopbackTransport()
    assert transport.write(b"\x1b\x40") == 2
    assert transport.write(b"\x00") == 1
    assert bytes(transport.written) == b"\x1b\x40\x00"


def test_read_returns_queued_replies_and_consumes_them():
    """read() returns up to n queued bytes and consumes what it returns."""
    transport = LoopbackTransport(replies=[b"\x80\x20", b"AB"])
    assert transport.read(2) == b"\x80\x20"
    assert transport.read(10) == b"AB"
    assert transport.read(1) == b""


def test_queue_reply_appends_more_canned_bytes():
    """queue_reply() adds bytes the printer should return on later reads."""
    transport = LoopbackTransport()
    transport.queue_reply(b"\x01\x02\x03")
    assert transport.read_exact(3) == b"\x01\x02\x03"


def test_read_exact_returns_requested_length():
    """read_exact() returns exactly n bytes and consumes them."""
    transport = LoopbackTransport(replies=[b"\x00" * 32])
    assert transport.read_exact(32) == b"\x00" * 32


def test_read_exact_raises_when_not_enough_queued():
    """read_exact() raises TransportTimeoutError when fewer than n bytes queued."""
    transport = LoopbackTransport(replies=[b"\x00" * 4])
    with pytest.raises(TransportTimeoutError):
        transport.read_exact(32)


def test_context_manager_opens_and_closes():
    """Using the transport as a context manager opens then closes it."""
    transport = LoopbackTransport()
    assert transport.opened is False
    with transport as ctx:
        assert ctx is transport
        assert transport.opened is True
    assert transport.opened is False
    assert transport.close_count == 1
