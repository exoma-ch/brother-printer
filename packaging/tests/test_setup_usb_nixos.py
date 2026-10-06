"""Tests for ``setup-usb.sh``'s NixOS and one-off grant paths (issue #63).

On NixOS none of the script's normal steps apply: there is no ``apt``/``dnf``/
``pacman``/``zypper``, ``/etc/udev/rules.d`` is a read-only symlink into the Nix
store, and there is no ``plugdev`` group. The script therefore detects NixOS,
skips those steps, offers a one-off ``chmod`` of the connected device node, and
prints the declarative rule for the user's system configuration.

None of that is testable by running it for real, so the script exposes a small
set of ``SETUP_USB_*`` path hooks (os-release, NixOS marker, sysfs, /dev/bus/usb,
udev rules dir). The tests point them at a fake host tree and put stub
executables (``sudo``, package managers, ``udevadm``, ``usermod``, …) ahead on
``PATH``, so both paths run end to end on any Linux host — including a non-NixOS
CI runner and a NixOS workstation, which must agree.
"""

from __future__ import annotations

import dataclasses
import os
import pathlib
import shlex
import stat
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "packaging" / "scripts" / "setup-usb.sh"

VENDOR_ID = "04f9"
PRODUCT_ID = "224b"

# Executables the script shells out to, stubbed so no test touches the real host.
# ``sudo`` is special-cased: it must exec its arguments so ``chmod``/``cp`` still
# run (inside the fake tree), while every privileged helper is only recorded.
STUBS = ("apt-get", "dnf", "pacman", "zypper", "udevadm", "usermod", "groupadd")


@dataclasses.dataclass(frozen=True)
class FakeHost:
    """A fake host tree plus the environment that points the script at it."""

    root: pathlib.Path
    env: dict[str, str]
    node: pathlib.Path
    udev_dir: pathlib.Path
    stub_log: pathlib.Path

    def calls(self) -> list[str]:
        """Names of stubbed executables the script invoked, in order."""
        if not self.stub_log.exists():
            return []
        return [
            line.split()[0]
            for line in self.stub_log.read_text().splitlines()
            if line.strip()
        ]

    def mode(self) -> int:
        return stat.S_IMODE(self.node.stat().st_mode)

    def run(self, *args: str, **kwargs: str) -> subprocess.CompletedProcess[str]:
        """Run the script end to end against this fake host."""
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env={**os.environ, **self.env, **kwargs},
        )

    def source(self, snippet: str, **kwargs: str) -> subprocess.CompletedProcess[str]:
        """Source the script (``main`` must not run) and evaluate a snippet."""
        program = f"set -euo pipefail\nsource {shlex.quote(str(SCRIPT))}\n{snippet}\n"
        return subprocess.run(
            ["bash", "-s"],
            input=program,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env={**os.environ, **self.env, **kwargs},
        )


@pytest.fixture
def host(tmp_path: pathlib.Path) -> FakeHost:
    """A fake non-NixOS host with a PT-E920BT on bus 3, device 19."""
    return _fake_host(tmp_path, nixos=False, printer=True)


def _fake_host(tmp_path: pathlib.Path, *, nixos: bool, printer: bool) -> FakeHost:
    root = tmp_path

    os_release = root / "os-release"
    os_release.write_text(
        "ID=nixos\nNAME=NixOS\n" if nixos else 'ID=ubuntu\nNAME="Ubuntu"\n'
    )

    marker = root / "NIXOS"
    if nixos:
        marker.write_text("")

    # Fake sysfs: a port directory with no attributes, a decoy device, and
    # (optionally) the printer. Bus/device numbers are unpadded, as in real sysfs.
    sysfs = root / "sys" / "bus" / "usb" / "devices"
    (sysfs / "usb3").mkdir(parents=True)
    _fake_usb_device(sysfs / "1-4", vendor="1d6b", product="0003", bus="1", dev="2")
    if printer:
        _fake_usb_device(
            sysfs / "3-2", vendor=VENDOR_ID, product=PRODUCT_ID, bus="3", dev="19"
        )

    dev_bus_usb = root / "dev" / "bus" / "usb"
    node = dev_bus_usb / "003" / "019"
    node.parent.mkdir(parents=True)
    node.write_text("")
    node.chmod(0o600)

    udev_dir = root / "etc" / "udev" / "rules.d"
    udev_dir.mkdir(parents=True)

    stub_log = root / "stub.log"
    stub_bin = _stub_bin(root / "bin", stub_log)

    env = {
        "SETUP_USB_OS_RELEASE": str(os_release),
        "SETUP_USB_NIXOS_MARKER": str(marker),
        "SETUP_USB_SYSFS_USB": str(sysfs),
        "SETUP_USB_DEV_BUS_USB": str(dev_bus_usb),
        "SETUP_USB_UDEV_DIR": str(udev_dir),
        "PATH": f"{stub_bin}{os.pathsep}{os.environ['PATH']}",
        # Deterministic plugdev target: a user that exists on no host, so the
        # "already a member" branch cannot be taken on a developer workstation.
        "SUDO_USER": "setup-usb-test-user",
    }
    return FakeHost(root=root, env=env, node=node, udev_dir=udev_dir, stub_log=stub_log)


def _fake_usb_device(
    path: pathlib.Path, *, vendor: str, product: str, bus: str, dev: str
) -> None:
    path.mkdir(parents=True)
    (path / "idVendor").write_text(f"{vendor}\n")
    (path / "idProduct").write_text(f"{product}\n")
    (path / "busnum").write_text(f"{bus}\n")
    (path / "devnum").write_text(f"{dev}\n")


def _stub_bin(path: pathlib.Path, stub_log: pathlib.Path) -> pathlib.Path:
    path.mkdir(parents=True)

    def write(name: str, body: str) -> None:
        script = path / name
        script.write_text(f"#!/usr/bin/env bash\n{body}\n")
        script.chmod(0o755)

    for name in STUBS:
        write(name, f'echo "{name} $*" >> {shlex.quote(str(stub_log))}')
    # sudo records the call, then runs the command so chmod/cp take effect.
    write("sudo", f'echo "sudo $*" >> {shlex.quote(str(stub_log))}\nexec "$@"')
    # No plugdev group on the fake host, so the script creates one.
    write("getent", f'echo "getent $*" >> {shlex.quote(str(stub_log))}\nexit 2')
    return path


def _rule_line(output: str) -> str:
    """The single udev rule line out of a block of prose."""
    lines = [line.strip() for line in output.splitlines() if "SUBSYSTEM==" in line]
    assert len(lines) == 1, f"expected exactly one rule line, got {lines!r}"
    return lines[0]


# --------------------------------------------------------------------------- #
# NixOS detection
# --------------------------------------------------------------------------- #


def test_nixos_detected_via_marker_file(tmp_path: pathlib.Path) -> None:
    """``/etc/NIXOS`` is the canonical marker."""
    nixos = _fake_host(tmp_path, nixos=True, printer=True)
    # Blind the os-release probe so the marker alone decides.
    result = nixos.source(
        "is_nixos && echo detected", SETUP_USB_OS_RELEASE=str(tmp_path / "absent")
    )
    assert result.returncode == 0, result.stderr
    assert "detected" in result.stdout


@pytest.mark.parametrize("id_line", ["ID=nixos", 'ID="nixos"'])
def test_nixos_detected_via_os_release(host: FakeHost, id_line: str) -> None:
    """``ID=nixos`` in os-release is detected, quoted or bare, with no marker."""
    os_release = host.root / "other-os-release"
    os_release.write_text(f'NAME=NixOS\n{id_line}\nVERSION_ID="26.05"\n')
    result = host.source(
        "is_nixos && echo detected",
        SETUP_USB_OS_RELEASE=str(os_release),
        SETUP_USB_NIXOS_MARKER=str(host.root / "absent"),
    )
    assert result.returncode == 0, result.stderr
    assert "detected" in result.stdout


def test_conventional_distribution_is_not_nixos(host: FakeHost) -> None:
    """A host with neither the marker nor ``ID=nixos`` is not NixOS."""
    result = host.source(
        "if is_nixos; then echo detected; else echo conventional; fi",
        SETUP_USB_NIXOS_MARKER=str(host.root / "absent"),
    )
    assert result.returncode == 0, result.stderr
    assert "conventional" in result.stdout
    assert "detected" not in result.stdout


# --------------------------------------------------------------------------- #
# Device node discovery via sysfs
# --------------------------------------------------------------------------- #


def test_find_device_node_derives_zero_padded_path(host: FakeHost) -> None:
    """Bus/device numbers from sysfs become ``/dev/bus/usb/003/019``."""
    result = host.source("find_device_node")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(host.node)


def test_find_device_node_fails_when_printer_absent(tmp_path: pathlib.Path) -> None:
    """With no PT-E920BT on the bus, discovery fails instead of guessing."""
    absent = _fake_host(tmp_path, nixos=True, printer=False)
    result = absent.source(
        "if find_device_node; then echo found; else echo missing; fi"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "missing"


# --------------------------------------------------------------------------- #
# The declarative rule the script prints for NixOS
# --------------------------------------------------------------------------- #


def test_declarative_rule_grants_via_group_and_mode(host: FakeHost) -> None:
    """The printed rule must use GROUP/MODE, not the inert ``uaccess`` tag.

    On NixOS ``TAG+="uaccess"`` is applied but never consumed: the
    ``RUN{builtin}+="uaccess"`` that installs the ACL lives in systemd's
    71-seat.rules / 73-seat-late.rules, which NixOS does not assemble into
    /etc/udev/rules.d. A reader following a ``uaccess`` rule ends up with a live
    rule and still no access.
    """
    result = host.source("print_nixos_rule")
    assert result.returncode == 0, result.stderr

    rule = _rule_line(result.stdout)
    assert f'ATTR{{idVendor}}=="{VENDOR_ID}"' in rule
    assert f'ATTR{{idProduct}}=="{PRODUCT_ID}"' in rule
    assert 'GROUP="lp"' in rule
    assert 'MODE="0660"' in rule
    assert "uaccess" not in rule

    assert "services.udev.extraRules" in result.stdout
    assert "extraGroups" in result.stdout  # group membership is half the grant
    assert "nixos-rebuild" in result.stdout


def test_declarative_rule_for_containers_is_world_writable(host: FakeHost) -> None:
    """``--devcontainer`` prints the MODE 0666 variant, which needs no group."""
    result = host.source("DEVCONTAINER=true\nprint_nixos_rule")
    assert result.returncode == 0, result.stderr

    rule = _rule_line(result.stdout)
    assert 'MODE="0666"' in rule
    assert "GROUP=" not in rule
    assert "extraGroups" not in result.stdout


# --------------------------------------------------------------------------- #
# End-to-end: the NixOS path
# --------------------------------------------------------------------------- #


def test_nixos_run_skips_package_manager_and_udev_install(
    tmp_path: pathlib.Path,
) -> None:
    """On NixOS the script installs nothing and explains itself instead."""
    nixos = _fake_host(tmp_path, nixos=True, printer=True)
    result = nixos.run()
    assert result.returncode == 0, result.stderr

    calls = nixos.calls()
    assert not [c for c in calls if c in {"apt-get", "dnf", "pacman", "zypper"}]
    assert "udevadm" not in calls
    assert "usermod" not in calls
    assert "groupadd" not in calls
    assert list(nixos.udev_dir.iterdir()) == []

    assert "NixOS" in result.stdout
    assert "nix develop" in result.stdout  # where libusb comes from instead
    assert "services.udev.extraRules" in result.stdout


def test_nixos_run_reports_the_connected_node(tmp_path: pathlib.Path) -> None:
    """The node path is derived for the user, not left to hand-assembly."""
    nixos = _fake_host(tmp_path, nixos=True, printer=True)
    result = nixos.run()
    assert result.returncode == 0, result.stderr
    assert str(nixos.node) in result.stdout


def test_nixos_run_does_not_chmod_without_confirmation(tmp_path: pathlib.Path) -> None:
    """Non-interactive and without ``--yes``, the grant is offered, not taken."""
    nixos = _fake_host(tmp_path, nixos=True, printer=True)
    result = nixos.run()
    assert result.returncode == 0, result.stderr
    assert nixos.mode() == 0o600
    assert "chmod" not in nixos.calls()
    # ... but the exact command is printed, so it is one copy-paste away.
    assert f"chmod 666 {nixos.node}" in result.stdout


def test_nixos_run_survives_a_disconnected_printer(tmp_path: pathlib.Path) -> None:
    """No printer plugged in still prints the declarative rule and exits 0."""
    nixos = _fake_host(tmp_path, nixos=True, printer=False)
    result = nixos.run()
    assert result.returncode == 0, result.stderr
    assert "services.udev.extraRules" in result.stdout


# --------------------------------------------------------------------------- #
# End-to-end: the one-off grant
# --------------------------------------------------------------------------- #


def test_one_off_grant_chmods_the_node(tmp_path: pathlib.Path) -> None:
    """``--one-off --yes`` opens the connected node and nothing else."""
    nixos = _fake_host(tmp_path, nixos=True, printer=True)
    result = nixos.run("--one-off", "--yes")
    assert result.returncode == 0, result.stderr
    assert nixos.mode() == 0o666

    calls = nixos.calls()
    assert "udevadm" not in calls
    assert "usermod" not in calls
    assert not [c for c in calls if c in {"apt-get", "dnf", "pacman", "zypper"}]
    assert list(nixos.udev_dir.iterdir()) == []
    assert "replug" in result.stdout.lower()  # the grant does not survive one


def test_one_off_grant_works_on_a_conventional_distribution(host: FakeHost) -> None:
    """The flag is not NixOS-specific — it is the portable escape hatch."""
    result = host.run("--one-off", "--yes")
    assert result.returncode == 0, result.stderr
    assert host.mode() == 0o666
    assert list(host.udev_dir.iterdir()) == []


def test_one_off_grant_fails_loudly_without_a_printer(tmp_path: pathlib.Path) -> None:
    """An explicit grant request with no device is an error, not a no-op."""
    absent = _fake_host(tmp_path, nixos=False, printer=False)
    result = absent.run("--one-off", "--yes")
    assert result.returncode != 0
    assert f"{VENDOR_ID}:{PRODUCT_ID}" in result.stderr


# --------------------------------------------------------------------------- #
# Regression: the conventional path is unchanged
# --------------------------------------------------------------------------- #


def test_conventional_host_still_installs_rule_and_plugdev(host: FakeHost) -> None:
    """NixOS support must not alter what a Debian/Ubuntu host gets."""
    result = host.run()
    assert result.returncode == 0, result.stderr

    installed = host.udev_dir / "99-brother-ptouch.rules"
    assert installed.exists()
    assert (
        installed.read_text()
        == (REPO_ROOT / "packaging" / "udev" / "99-brother-ptouch.rules").read_text()
    )

    calls = host.calls()
    assert "apt-get" in calls
    assert "udevadm" in calls
    assert "groupadd" in calls
    assert "usermod" in calls
    assert "services.udev.extraRules" not in result.stdout


def test_devcontainer_rule_still_installed_on_conventional_host(host: FakeHost) -> None:
    """``--devcontainer`` keeps installing the 0666 rule and skipping plugdev."""
    result = host.run("--devcontainer")
    assert result.returncode == 0, result.stderr

    assert (host.udev_dir / "99-brother-ptouch_devcontainer.rules").exists()
    assert "usermod" not in host.calls()
