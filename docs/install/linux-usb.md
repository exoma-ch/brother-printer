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

## Verifying from the development shell

Hardware verification runs on the host, in the project's Nix dev shell. The
repository moved from a devcontainer to `direnv` mode precisely because of this
device: the shared container image is Nix-built with no `apt`, and `libusb` is
not on the toolchain's package list, so there was no supported way to put the
pyusb backend inside it. On the host there is no device passthrough, no
rootless-Podman uid remapping and no container-specific udev rule to maintain —
the printer is simply the host's printer.

Enter the shell (`direnv allow` does this automatically on `cd`):

```bash
nix develop        # or: direnv allow
```

`flake.nix` adds `pkgs.libusb1` and puts it on `LD_LIBRARY_PATH`, because pyusb
resolves the backend through `ctypes.util.find_library` at import time — being
in the closure is not enough. Confirm both:

```bash
# libusb discoverable by ctypes (what pyusb actually does)
python3 -c "import ctypes.util; print(ctypes.util.find_library('usb-1.0'))"

# libusb backend loaded
uv run python -c "import usb.backend.libusb1 as b; print(b.get_backend())"
```

### Host setup

The dev shell supplies `libusb`, so the only thing still needed from the host is
permission to open the device node. Without it, enumeration succeeds and
`open()` fails with permission denied.

**On a conventional distribution**, this is the same setup an end user performs
— install the rule and join `plugdev`:

```bash
./packaging/scripts/setup-usb.sh        # or: just setup-usb
```

See [Quick setup (script)](#quick-setup-script) for what it does and
[Prerequisites](#prerequisites) for the manual equivalent.

**On NixOS, that script does not apply.** It installs `libusb` through
`apt`/`dnf`/`pacman`/`zypper`, which NixOS has none of, and it writes to
`/etc/udev/rules.d`, which is a read-only symlink into the Nix store. There is
also no `plugdev` group unless the system configuration creates one. Declare the
rule in your system configuration instead and rebuild — either inline:

```nix
services.udev.extraRules = ''
  SUBSYSTEM=="usb", ATTR{idVendor}=="04f9", ATTR{idProduct}=="224b", TAG+="uaccess"
'';
```

or by adding a package carrying
[99-brother-ptouch.rules](../../packaging/udev/99-brother-ptouch.rules) to
`services.udev.packages`. `TAG+="uaccess"` grants the locally logged-in user
access through systemd-logind, which avoids needing a `plugdev` group at all.

**For a single verification run**, with no system change, chmod the node after
plugging the printer in:

```bash
lsusb -d 04f9:                          # PT-E920BT is 04f9:224b; note Bus/Device
sudo chmod 666 /dev/bus/usb/<bus>/<device>
```

This is lost on replug, which is fine for a one-off hardware check and avoids a
rebuild.

Afterwards, confirm the node is openable:

```bash
ls -l /dev/bus/usb/<bus>/<device>       # expect crw-rw-rw- or crw-rw-r--+
```

### Verify

With the PT-E920BT connected and powered on:

```bash
just discover            # library-level device discovery
just printer-status      # live status: loaded tape, errors
just test-connect        # non-destructive checks, consumes no tape
just test-hardware       # full opt-in hardware suite (consumes tape)
```

## Running the driver inside a container

This section is for *using* the driver in a container, not for developing this
repository — the project has no devcontainer. The notes are kept because
rootless Podman needs more than the standard rule.

Bind-mount the host USB device tree; enumeration via `/sys` alone is not enough
for string descriptors or I/O:

```yaml
volumes:
  - /dev/bus/usb:/dev/bus/usb
```

Rootless Podman supports neither `device_cgroup_rules` (container create fails)
nor Docker's `group_add: keep-groups` (Podman looks up a group literally named
`keep-groups`). It also remaps bind-mounted nodes to `nobody:nogroup`, so mode
`0664` leaves container processes with read-only `other::r--` access — which
makes enumeration succeed while `open()` fails with permission denied.

Install the container rule, which sets `MODE="0666"`:

```bash
sudo cp packaging/udev/99-brother-ptouch_devcontainer.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Replug, then confirm `crw-rw-rw-` on the host node. The `_devcontainer` suffix
sorts after [99-brother-ptouch.rules](../../packaging/udev/99-brother-ptouch.rules)
so it wins where both are installed; remove any older hyphenated copy.
`setup-usb.sh --devcontainer` performs these steps and skips `plugdev`.

Fallbacks, in order of preference:

1. The `MODE="0666"` rule above — durable across replug.
2. `sudo chmod 666 /dev/bus/usb/<bus>/<device>` — one-off, lost on replug.
3. [99-brother-ptouch.rules](../../packaging/udev/99-brother-ptouch.rules) with
   `plugdev` membership — correct for host CLI use, not sufficient on its own
   inside rootless Podman.

Rootful Docker users who hit a device-cgroup deny on bind-mounted nodes can add
`device_cgroup_rules: ["c 189:* rwm"]` to their own compose override.
