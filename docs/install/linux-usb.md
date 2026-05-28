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

## Verifying inside the devcontainer (rootless Podman)

The project devcontainer bind-mounts the host USB device tree so pyusb can open
device nodes (enumeration via `/sys` alone is not enough for string descriptors
or I/O). Configuration lives in
[.devcontainer/docker-compose.project.yaml](../../.devcontainer/docker-compose.project.yaml):

```yaml
volumes:
  - /dev/bus/usb:/dev/bus/usb
group_add:
  - plugdev
```

The libusb backend is installed on container create via
[.devcontainer/scripts/post-create.sh](../../.devcontainer/scripts/post-create.sh).

### Host setup (run on the Linux host, not inside the container)

1. Install the udev rule (see above) and replug the printer.
2. Confirm the device appears: `lsusb -d 04f9:`
3. Check permissions on the device node:
   `ls -l /dev/bus/usb/<bus>/<device>` and optionally `getfacl` on that path.

### Recreate the devcontainer

After changing compose overrides, rebuild so passthrough and post-create run:

- VS Code: **Dev Containers: Rebuild Container**, or
- Host: `podman compose -f .devcontainer/docker-compose.yml -f .devcontainer/docker-compose.project.yaml -f .devcontainer/docker-compose.local.yaml up -d --force-recreate`

### Verify from inside the container

With the PT-E920BT connected and powered on:

```bash
# libusb backend loaded
uv run python -c "import usb.backend.libusb1 as b; print(b.get_backend())"

# USB device tree visible
test -d /dev/bus/usb && ls /dev/bus/usb

# Library discovery
brother-printer discover

# Opt-in hardware tests (requires a connected printer)
just test-hardware
```

### Permission fallbacks (rootless Podman)

If `discover` works but `UsbTransport.open()` fails with permission denied:

1. **uaccess (preferred):** the shipped udev rule sets `TAG+="uaccess"` so the
   active desktop session user gets an ACL on the device node.
2. **plugdev group:** add your host user to `plugdev`, log out/in, and ensure
   `group_add: plugdev` is present in the compose override.
3. **Temporary dev-only rule:** `MODE="0666"` on the udev rule for local
   debugging only — do not commit that change.

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
