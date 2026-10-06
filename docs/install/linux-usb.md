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
2. **Detects NixOS** — where none of the steps below apply. It then skips the
   package manager, offers a one-off grant on the connected printer, and prints
   the rule to declare in your system configuration; see
   [NixOS hosts](#nixos-hosts). The remaining steps are the
   conventional-distribution path.
3. **Installs libusb** — detects your package manager (`apt`, `dnf`, `pacman`,
   or `zypper`) and installs the libusb runtime that pyusb needs. Skip with
   `--no-libusb` if it is already present.
4. **Installs the udev rule** — copies the appropriate rule into
   `/etc/udev/rules.d/`, then runs `udevadm control --reload` and
   `udevadm trigger`. From a checkout it copies the local file; standalone it
   downloads the rule from GitHub (override the ref with `--ref` or `REF=`).
5. **Configures `plugdev`** — creates the group if needed and adds your user, so
   non-root processes can open the device. Skipped for devcontainer mode.
6. **Prints next steps** — replug the printer and verify with `discover`.

### Options

The script installs libusb, copies the udev rule, reloads udev, and adds your
user to `plugdev`. For devcontainer hosts use `--devcontainer` (installs the
`MODE="0666"` rule and skips `plugdev`). `--one-off` skips all of that and
instead grants access on the currently connected printer by `chmod`-ing its
`/dev/bus/usb` node — no system change, lost on replug, useful for a single
hardware check and the only option on a host where udev rules are not yours to
install (add `--yes` to skip the confirmation). Because piping to `bash` cannot
pass flags, download the script first:

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

On NixOS, libusb comes from the dev shell or your own profile instead — see
[NixOS hosts](#nixos-hosts).

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

## NixOS hosts

None of the steps above apply on NixOS: there is no distribution package
manager, `/etc/udev/rules.d` is a read-only symlink into the Nix store, and
there is no `plugdev` group. Run the script anyway — it detects NixOS, locates
the connected printer, and prints what to do instead of installing nothing:

```bash
./packaging/scripts/setup-usb.sh        # or: just setup-usb
```

**libusb** comes from the dev shell in a checkout (`nix develop`, or
`direnv allow`); otherwise add `pkgs.libusb1` to your profile or
`environment.systemPackages`.

**Durable access** is a system-configuration change, which a driver's install
script has no business making. Declare the rule yourself:

```nix
services.udev.extraRules = ''
  SUBSYSTEM=="usb", ATTR{idVendor}=="04f9", ATTR{idProduct}=="224b", GROUP="lp", MODE="0660"
'';
users.users.<you>.extraGroups = [ "lp" ];
```

Then `sudo nixos-rebuild switch`. Group membership takes effect at login, so log
out and back in afterwards (`newgrp lp` covers a single shell). `MODE="0666"`
needs neither the group nor the re-login, at the cost of exposing the device to
every local process.

Set `GROUP` explicitly rather than leaning on the `root:lp` ownership the node
already arrives with: that comes from udev's built-in printer-class default, not
from any rule in the assembled set, so it is not a contract to depend on.

> **Do not use `TAG+="uaccess"` on NixOS.** It is the normally-correct modern
> mechanism — systemd-logind puts an ACL for the active local session's user on
> the node, so no group is needed — and it is what
> [99-brother-ptouch.rules](../../packaging/udev/99-brother-ptouch.rules)
> carries for conventional distributions. On NixOS the tag is applied and
> nothing consumes it: the `RUN{builtin}+="uaccess"` that installs the ACL ships
> in systemd's `71-seat.rules` and `73-seat-late.rules`, neither of which NixOS
> assembles into `/etc/udev/rules.d`. The rule goes live, `udevadm info` shows
> the tag, `getfacl` shows no ACL for your user, and `open()` still fails with
> permission denied.

Adding a package that carries
[99-brother-ptouch.rules](../../packaging/udev/99-brother-ptouch.rules) to
`services.udev.packages` works too, but that rule grants `GROUP="plugdev"`, so
the group has to exist and contain you:

```nix
users.groups.plugdev = { };
users.users.<you>.extraGroups = [ "plugdev" ];
```

**For a single verification run**, with no system change and no rebuild, grant
access on the connected node:

```bash
./packaging/scripts/setup-usb.sh --one-off      # add --yes to skip the prompt
```

The script derives `/dev/bus/usb/<bus>/<device>` from sysfs — `lsusb` is not
installed by default on NixOS, and the numbers change on every replug — then
`chmod 666`s it after confirming. The grant is lost on replug or power-cycle,
which is fine for a hardware check. Confirm it took:

```bash
ls -l /dev/bus/usb/<bus>/<device>       # expect crw-rw-rw-
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

**On NixOS the same script runs, but installs nothing** — it has no package
manager to install `libusb` with, `/etc/udev/rules.d` is a read-only Nix store
symlink, and there is no `plugdev` group. It detects that, offers a one-off grant
on the connected printer, and prints the rule to declare in your system
configuration. The dev shell already covers `libusb`, so the rule (or the one-off
grant) is all that is left:

```bash
./packaging/scripts/setup-usb.sh --one-off      # this session only
```

See [NixOS hosts](#nixos-hosts) for the declarative rule, and why it must grant
through `GROUP`/`MODE` rather than `TAG+="uaccess"`.

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
2. `./packaging/scripts/setup-usb.sh --one-off` (equivalently
   `sudo chmod 666 /dev/bus/usb/<bus>/<device>`) — one-off, lost on replug.
3. [99-brother-ptouch.rules](../../packaging/udev/99-brother-ptouch.rules) with
   `plugdev` membership — correct for host CLI use, not sufficient on its own
   inside rootless Podman.

Rootful Docker users who hit a device-cgroup deny on bind-mounted nodes can add
`device_cgroup_rules: ["c 189:* rwm"]` to their own compose override.
