# Linux USB setup

v0.1 targets Linux hosts with USB access to the Brother PT-E920BT. USB vendor
identifiers are documented in [docs/vendor/usb-ids.md](../vendor/usb-ids.md).

## Prerequisites

Install the system libusb library (pyusb uses it via ctypes):

```bash
# Debian / Ubuntu
sudo apt install libusb-1.0-0

# Fedora
sudo dnf install libusb
```

Install the Python package (includes the `brother-printer` CLI):

```bash
uv sync
# or: pip install .
```

## udev rules (non-root access)

Copy the sample rule from this repository:

```bash
sudo cp packaging/udev/99-brother-ptouch.rules /etc/udev/rules.d/
sudo udevadm control --reload
sudo udevadm trigger
```

Add your user to the `plugdev` group (log out and back in afterward):

```bash
sudo usermod -aG plugdev "$USER"
```

## Verify discovery

Connect the PT-E920BT over USB, then:

```bash
brother-printer discover
```

Expected output (one line per printer):

```text
04f9:xxxx#<serial>  PT-E920BT   <bus>:<address>
```

## Troubleshooting

### Permission denied

If `brother-printer discover` or transport open fails with a permission error,
install the udev rule above and confirm group membership. The CLI error message
includes a pointer to this document.

### Device busy

Another process (often the CUPS `usblp` kernel driver) may have claimed the
device. Unplug and replug the printer, stop conflicting print jobs, or detach
the kernel driver (the library attempts this automatically on `open()`).

### No device found

- Confirm the printer is powered on and connected via USB.
- Run `lsusb -d 04f9:` and check that the product string is `PT-E920BT`.
- Only PT-E920BT devices are listed; other Brother models are ignored by design.
