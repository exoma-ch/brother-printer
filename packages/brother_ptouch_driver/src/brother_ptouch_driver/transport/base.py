"""Transport protocol and printer discovery metadata."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class Transport(Protocol):
    """Byte-level I/O to a Brother P-touch printer."""

    def open(self) -> None:
        """Open the transport connection."""
        ...

    def close(self) -> None:
        """Close the transport connection."""
        ...

    def write(self, data: bytes) -> int:
        """Write bytes to the printer. Returns number of bytes written."""
        ...

    def read(self, n: int, timeout_ms: int | None = None) -> bytes:
        """Read up to n bytes from the printer."""
        ...

    def read_exact(self, n: int, timeout_ms: int | None = None) -> bytes:
        """Read exactly n bytes, raising on timeout before n arrive."""
        ...


@dataclass(frozen=True)
class PrinterInfo:
    """Metadata for a discovered Brother P-touch printer."""

    vendor_id: int
    product_id: int
    serial: str | None
    product: str
    bus: int
    address: int

    @property
    def identifier(self) -> str:
        """Stable identifier string for CLI and library consumers."""
        vid = f"{self.vendor_id:04x}"
        pid = f"{self.product_id:04x}"
        suffix = self.serial if self.serial else f"{self.bus}:{self.address}"
        return f"{vid}:{pid}#{suffix}"
