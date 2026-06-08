"""Tests for the Transport protocol and PrinterInfo dataclass."""

from dataclasses import dataclass

import pytest

from brother_ptouch_driver.transport.base import PrinterInfo, Transport


@dataclass
class _TransportStub:
    """Minimal in-memory transport for protocol conformance checks."""

    _buffer: bytearray

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def write(self, data: bytes) -> int:
        self._buffer.extend(data)
        return len(data)

    def read(self, n: int, timeout_ms: int | None = None) -> bytes:
        chunk = bytes(self._buffer[:n])
        del self._buffer[:n]
        return chunk

    def read_exact(self, n: int, timeout_ms: int | None = None) -> bytes:
        return self.read(n, timeout_ms)


def test_transport_protocol_is_runtime_checkable():
    """Transport is a runtime-checkable Protocol."""
    stub = _TransportStub(_buffer=bytearray())
    assert isinstance(stub, Transport)


def test_transport_stub_open_write_read_close():
    """A conforming stub can open, write, read, and close."""
    stub = _TransportStub(_buffer=bytearray())
    stub.open()
    assert stub.write(b"\x01\x02") == 2
    assert stub.read(2) == b"\x01\x02"
    stub.close()


def test_printer_info_identifier_with_serial():
    """PrinterInfo.identifier includes VID, PID, and serial."""
    info = PrinterInfo(
        vendor_id=0x04F9,
        product_id=0x20C7,
        serial="000123456789",
        product="PT-E920BT",
        bus=1,
        address=5,
    )
    assert info.identifier == "04f9:20c7#000123456789"


def test_printer_info_identifier_without_serial():
    """PrinterInfo.identifier falls back to bus:address when serial is missing."""
    info = PrinterInfo(
        vendor_id=0x04F9,
        product_id=0x20C7,
        serial=None,
        product="PT-E920BT",
        bus=2,
        address=7,
    )
    assert info.identifier == "04f9:20c7#2:7"


def test_printer_info_is_frozen():
    """PrinterInfo is immutable."""
    info = PrinterInfo(
        vendor_id=0x04F9,
        product_id=0x20C7,
        serial="000123456789",
        product="PT-E920BT",
        bus=1,
        address=5,
    )
    with pytest.raises(AttributeError):
        info.product = "other"  # type: ignore[misc]
