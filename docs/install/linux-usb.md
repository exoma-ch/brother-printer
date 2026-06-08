# Linux USB setup

v0.1 targets Linux hosts with USB access to the Brother PT-E920BT. USB vendor
identifiers are documented in [docs/vendor/usb-ids.md](../vendor/usb-ids.md).

## Quick setup (script)

From a repository checkout:

```bash
./packaging/scripts/setup-usb.sh        # or: just setup-usb
```

Standalone (no checkout — e.g. host setup before running a container):

```bash
curl -fsSL https://raw.githubusercontent.com/exoma-ch/brother-printer/main/packaging/scripts/setup-usb.sh | bash
```

### What the script does

`setup-usb.sh` automates the manual steps documented below. In order, it:

1. **Checks the platform** — exits early if not running on Linux, and resolves
   `sudo` (or runs directly when already root).
2. **Installs libusb** — detects your package manager (`apt`, `dnf`, `pacman`,
   or `zypper`) and installs the libusb runtime that pyusb needs. Skip with
   `--no-libusb` if it is already present.
3. **Installs the udev rule** — copies the appropriate rule into
   `/etc/udev/rules.d/`, then runs `udevadm control --reload` and
   `udevadm trigger`. From a checkout it copies the local file; standalone it
   downloads the rule from GitHub (override the ref with `--ref` or `REF=`).
4. **Configures `plugdev`** — creates the group if needed and adds your user, so
   non-root processes can open the device. Skipped for devcontainer mode.
5. **Prints next steps** — replug the printer and verify with `discover`.

### Options

The script installs libusb, copies the udev rule, reloads udev, and adds your
user to `plugdev`. For devcontainer hosts use `--devcontainer` (installs the
`MODE="0666"` rule and skips `plugdev`). Because piping to `bash` cannot pass
flags, download the script first:

```bash
curl -fsSL https://raw.githubusercontent.com/exoma-ch/brother-printer/main/packaging/scripts/setup-usb.sh \
  -o setup-usb.sh && bash setup-usb.sh --devcontainer
```

For the full flag reference, run `./packaging/scripts/setup-usb.sh --help` (or
`just setup-usb -- --help`). The manual steps below remain canonical if you
prefer to install piece by piece.

## Prerequisites

Install the system libusb library (pyusb uses it via ctypes):

```bash
# Debian / Ubuntu
sudo apt install libusb-1.0-0

# Fedora
sudo dnf install libusb
```

Install the Python package (includes the `brother-ptouch-driver` CLI):

```bash
uv sync --all-packages
# or: pip install .
```

Run the CLI via `uv run` (or activate the project venv first):

```bash
uv run brother-ptouch-driver --help
```

## udev rules (non-root access)

Copy the sample rule from this repository:

```bash
sudo cp packaging/udev/99-brother-ptouch.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Add your user to the `plugdev` group (log out and back in afterward):

```bash
sudo usermod -aG plugdev "$USER"
```

## Verify discovery

Connect the PT-E920BT over USB, then:

```bash
uv run brother-ptouch-driver discover
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
```

Rootless Podman does not support `device_cgroup_rules` (container create fails) or
Docker's `group_add: keep-groups` (Podman looks up a group named `keep-groups`).
USB access relies on the bind mount and the devcontainer udev rule (`MODE="0666"`).
Rootful Docker users who hit a device-cgroup deny on bind-mounted nodes may add
`device_cgroup_rules: ["c 189:* rwm"]` to a personal
[`.devcontainer/docker-compose.local.yaml`](../../.devcontainer/docker-compose.local.yaml)
(gitignored).

The libusb backend is installed on container create via
[.devcontainer/scripts/post-create.sh](../../.devcontainer/scripts/post-create.sh).

### Host setup (run on the Linux host, not inside the container)

1. Install the **devcontainer udev rule** (rootless Podman remaps USB nodes to
   `nobody:nogroup` inside the container; mode `0664` leaves container processes
   with read-only access). From the repo root:

   ```bash
   sudo cp packaging/udev/99-brother-ptouch_devcontainer.rules /etc/udev/rules.d/
   sudo udevadm control --reload-rules && sudo udevadm trigger
   ```

   Unplug and replug the printer. Confirm world-writable access on the host:

   ```bash
   lsusb | grep -i 04f9                    # note Bus and Device numbers
   ls -l /dev/bus/usb/<bus>/<device>       # expect crw-rw-rw-
   ```

   If mode is still `664`, the standard rule may have loaded after the
   devcontainer rule — remove the old hyphenated copy if present, ensure only
   `99-brother-ptouch.rules` and `99-brother-ptouch_devcontainer.rules` are
   installed (the `_devcontainer` suffix sorts last and wins).

   For normal (non-container) CLI use on the host, keep
   [99-brother-ptouch.rules](../../packaging/udev/99-brother-ptouch.rules)
   (`0664` + `plugdev`) instead.

2. Confirm the device appears: `lsusb -d 04f9:` (PT-E920BT is `04f9:224b`).
3. Check permissions on the device node after replug.

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
uv run brother-ptouch-driver discover

# Opt-in hardware tests (requires a connected printer)
just test-hardware
```

### Permission fallbacks (rootless Podman)

If enumeration finds the device (`lsusb`, pyusb `find`) but `discover` returns
nothing or `open()` fails with permission denied, the bind-mounted node is
likely `nobody:nogroup` with mode `0664` (container processes only get
`other::r--`):

1. **Devcontainer udev rule (recommended for dev):** install
   [99-brother-ptouch_devcontainer.rules](../../packaging/udev/99-brother-ptouch_devcontainer.rules)
   (`MODE="0666"`), replug, verify `crw-rw-rw-` on the host node.
2. **One-off test without udev change:** `sudo chmod 666 /dev/bus/usb/<bus>/<device>`
   (lost on replug).
3. **Normal host CLI:** use [99-brother-ptouch.rules](../../packaging/udev/99-brother-ptouch.rules)
   with `plugdev` group membership — not sufficient alone inside rootless Podman.

## Troubleshooting

### Permission denied

If `uv run brother-ptouch-driver discover` or transport open fails with a permission error,
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
