#!/usr/bin/env bash
# Install libusb and udev rules for non-root Brother PT-E920BT USB access on Linux.
#
# Run from a repository checkout or standalone (curl from GitHub):
#   ./packaging/scripts/setup-usb.sh
#   curl -fsSL https://raw.githubusercontent.com/exoma-ch/brother-printer/main/packaging/scripts/setup-usb.sh | bash
#
# For flags (--devcontainer, --one-off, --ref, etc.) download first, then execute:
#   curl -fsSL .../setup-usb.sh -o setup-usb.sh && bash setup-usb.sh --devcontainer
#
# NixOS is detected and takes a different path: none of the install steps apply
# there (no distribution package manager, /etc/udev/rules.d is a read-only Nix
# store symlink, and there is no plugdev group), so the script offers a one-off
# grant on the connected device node and prints the declarative rule to add to
# the system configuration. Refs: #63

set -euo pipefail

readonly REPO="exoma-ch/brother-printer"
readonly DEFAULT_REF="${REF:-main}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
readonly SCRIPT_DIR

readonly VENDOR_ID="04f9"
readonly PRODUCT_ID="224b"
readonly ONE_OFF_MODE="666"

# Host paths. Overridable so the NixOS and one-off paths can be exercised on any
# Linux host (see packaging/tests/test_setup_usb_nixos.py); not user-facing
# options.
readonly UDEV_DIR="${SETUP_USB_UDEV_DIR:-/etc/udev/rules.d}"
readonly OS_RELEASE="${SETUP_USB_OS_RELEASE:-/etc/os-release}"
readonly NIXOS_MARKER="${SETUP_USB_NIXOS_MARKER:-/etc/NIXOS}"
readonly SYSFS_USB="${SETUP_USB_SYSFS_USB:-/sys/bus/usb/devices}"
readonly DEV_BUS_USB="${SETUP_USB_DEV_BUS_USB:-/dev/bus/usb}"

DEVCONTAINER=false
NO_LIBUSB=false
ONE_OFF=false
ASSUME_YES=false
GRANTED_ONE_OFF=false
GIT_REF="$DEFAULT_REF"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Install libusb and udev rules for non-root Brother PT-E920BT USB access on Linux.

On NixOS the install steps do not apply: the script skips them, offers a one-off
grant on the connected printer, and prints the rule to declare in your system
configuration.

Options:
  --devcontainer   Install the devcontainer udev rule (MODE 0666) instead of
                   the standard host rule (0664 + plugdev). Skips plugdev setup.
  --no-libusb      Skip libusb prerequisite installation.
  --one-off        Grant access on the currently connected printer by chmod-ing
                   its $DEV_BUS_USB node, and do nothing else: no libusb, no
                   udev rule, no group. Lost on replug; needs no udev rule and
                   no rebuild, so it works on any distribution.
  -y, --yes        Assume yes for the one-off grant confirmation.
  --ref <git-ref>  Git ref for standalone udev rule download (default: $DEFAULT_REF).
                   Also settable via REF environment variable.
  -h, --help       Show this help and exit.

Examples:
  # From a repository checkout
  ./packaging/scripts/setup-usb.sh

  # One-off grant for a single hardware check (no system change)
  ./packaging/scripts/setup-usb.sh --one-off

  # Standalone (no flags via pipe; download first for options)
  curl -fsSL https://raw.githubusercontent.com/$REPO/main/packaging/scripts/setup-usb.sh | bash
  curl -fsSL https://raw.githubusercontent.com/$REPO/main/packaging/scripts/setup-usb.sh \\
    -o setup-usb.sh && bash setup-usb.sh --devcontainer
EOF
}

log() {
    echo "==> $*"
}

note() {
    echo "    $*"
}

warn() {
    echo "warning: $*" >&2
}

die() {
    echo "error: $*" >&2
    exit 1
}

require_linux() {
    if [[ "$(uname -s)" != "Linux" ]]; then
        die "this script supports Linux only"
    fi
}

require_sudo() {
    if [[ $EUID -eq 0 ]]; then
        SUDO=""
    elif command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
    else
        die "root privileges required; run as root or install sudo"
    fi
}

# True on NixOS, where the package-manager, /etc/udev/rules.d and plugdev steps
# are all inapplicable.
is_nixos() {
    [[ -e "$NIXOS_MARKER" ]] && return 0
    [[ -r "$OS_RELEASE" ]] && grep -Eq '^ID="?nixos"?$' "$OS_RELEASE"
}

# Ask before a privileged change. Declines when stdin is not a terminal, so an
# unattended run never blocks on a prompt nobody can answer; --yes overrides.
confirm() {
    local reply

    if [[ "$ASSUME_YES" == true ]]; then
        return 0
    fi

    if [[ ! -t 0 ]]; then
        return 1
    fi

    read -r -p "==> $1 [y/N] " reply
    [[ "$reply" == [yY] || "$reply" == [yY][eE][sS] ]]
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --devcontainer)
                DEVCONTAINER=true
                shift
                ;;
            --no-libusb)
                NO_LIBUSB=true
                shift
                ;;
            --one-off)
                ONE_OFF=true
                shift
                ;;
            -y | --yes)
                ASSUME_YES=true
                shift
                ;;
            --ref)
                [[ $# -ge 2 ]] || die "--ref requires a value"
                GIT_REF="$2"
                shift 2
                ;;
            -h | --help)
                usage
                exit 0
                ;;
            *)
                die "unknown option: $1 (try --help)"
                ;;
        esac
    done
}

install_libusb() {
    if [[ "$NO_LIBUSB" == true ]]; then
        log "skipping libusb installation (--no-libusb)"
        return 0
    fi

    if is_nixos; then
        log "NixOS detected: skipping libusb installation"
        note "there is no distribution package manager to install it with."
        note "In a checkout the dev shell supplies it:"
        note "  nix develop        # or: direnv allow"
        note "Otherwise add pkgs.libusb1 to your profile or systemPackages."
        return 0
    fi

    log "installing libusb prerequisite"

    if command -v apt-get >/dev/null 2>&1; then
        $SUDO apt-get update -qq
        $SUDO apt-get install -y --no-install-recommends libusb-1.0-0
    elif command -v dnf >/dev/null 2>&1; then
        $SUDO dnf install -y libusb
    elif command -v pacman >/dev/null 2>&1; then
        $SUDO pacman -Sy --noconfirm libusb
    elif command -v zypper >/dev/null 2>&1; then
        $SUDO zypper install -y libusb-1_0-0
    else
        warn "no supported package manager found; install libusb manually"
        warn "  Debian/Ubuntu: sudo apt install libusb-1.0-0"
        warn "  Fedora:        sudo dnf install libusb"
    fi
}

rule_filename() {
    if [[ "$DEVCONTAINER" == true ]]; then
        echo "99-brother-ptouch_devcontainer.rules"
    else
        echo "99-brother-ptouch.rules"
    fi
}

resolve_rule_source() {
    local rule
    rule="$(rule_filename)"
    local local_path="$SCRIPT_DIR/../udev/$rule"

    if [[ -f "$local_path" ]]; then
        echo "$local_path"
        return 0
    fi

    echo "https://raw.githubusercontent.com/$REPO/$GIT_REF/packaging/udev/$rule"
}

install_udev_rule() {
    local rule source dest
    rule="$(rule_filename)"
    source="$(resolve_rule_source)"
    dest="$UDEV_DIR/$rule"

    log "installing udev rule: $rule"

    if [[ "$source" == http* ]]; then
        log "fetching rule from $source"
        $SUDO curl -fsSL "$source" -o "$dest"
    else
        $SUDO cp "$source" "$dest"
    fi

    $SUDO udevadm control --reload-rules
    $SUDO udevadm trigger
}

setup_plugdev() {
    if [[ "$DEVCONTAINER" == true ]]; then
        log "skipping plugdev setup (--devcontainer)"
        return 0
    fi

    local target_user="${SUDO_USER:-${USER:-}}"

    if [[ -z "$target_user" || "$target_user" == "root" ]]; then
        warn "could not determine non-root user; add yourself to plugdev manually:"
        warn "  sudo usermod -aG plugdev \$USER"
        return 0
    fi

    log "configuring plugdev group for $target_user"

    if ! getent group plugdev >/dev/null 2>&1; then
        $SUDO groupadd -f plugdev
    fi

    local added=false
    if id -nG "$target_user" 2>/dev/null | tr ' ' '\n' | grep -qx plugdev; then
        log "$target_user is already in plugdev"
    else
        $SUDO usermod -aG plugdev "$target_user"
        added=true
        log "added $target_user to plugdev"
    fi

    if [[ "$added" == true ]]; then
        warn "log out and back in (or run 'newgrp plugdev') for group membership to take effect"
    fi
}

# Path of the connected printer's USB node, derived from sysfs. Beats asking the
# user for it: bus and device numbers change on every replug.
find_device_node() {
    local dir bus dev

    for dir in "$SYSFS_USB"/*; do
        [[ -r "$dir/idVendor" && -r "$dir/idProduct" ]] || continue
        [[ "$(<"$dir/idVendor")" == "$VENDOR_ID" ]] || continue
        [[ "$(<"$dir/idProduct")" == "$PRODUCT_ID" ]] || continue
        [[ -r "$dir/busnum" && -r "$dir/devnum" ]] || continue

        bus="$(<"$dir/busnum")"
        dev="$(<"$dir/devnum")"
        # 10# forces base 10: the node path is zero-padded, and printf would
        # otherwise read a padded value back as octal.
        printf '%s/%03d/%03d\n' "$DEV_BUS_USB" "$((10#$bus))" "$((10#$dev))"
        return 0
    done

    return 1
}

# chmod the live device node. Needs no udev rule and no reboot or rebuild, and is
# lost on replug — enough for one hardware check.
grant_one_off() {
    local node

    if ! node="$(find_device_node)"; then
        warn "no PT-E920BT ($VENDOR_ID:$PRODUCT_ID) found on the USB bus"
        warn "  plug the printer in, switch it on, and re-run"
        return 1
    fi

    log "printer found at $node"

    if ! confirm "grant access now with 'chmod $ONE_OFF_MODE $node'?"; then
        log "one-off grant not applied; run it yourself when you want it:"
        note "sudo chmod $ONE_OFF_MODE $node"
        return 0
    fi

    $SUDO chmod "$ONE_OFF_MODE" "$node"
    GRANTED_ONE_OFF=true
    log "granted mode $ONE_OFF_MODE on $node"
}

# The durable grant on NixOS is a system-configuration change, which a driver's
# install script has no business making — so print it instead of pretending to
# install it.
print_nixos_rule() {
    local rule="SUBSYSTEM==\"usb\", ATTR{idVendor}==\"$VENDOR_ID\", ATTR{idProduct}==\"$PRODUCT_ID\""

    if [[ "$DEVCONTAINER" == true ]]; then
        rule+=", MODE=\"0666\""
    else
        rule+=", GROUP=\"lp\", MODE=\"0660\""
    fi

    cat <<EOF

For access that survives a replug, declare the rule in your NixOS configuration
($UDEV_DIR is a read-only symlink into the Nix store, so this script
cannot install it):

  services.udev.extraRules = ''
    $rule
  '';
EOF

    if [[ "$DEVCONTAINER" != true ]]; then
        cat <<EOF
  users.users.<you>.extraGroups = [ "lp" ];
EOF
    fi

    cat <<EOF

Apply it with 'sudo nixos-rebuild switch'.
EOF

    if [[ "$DEVCONTAINER" != true ]]; then
        cat <<EOF
Group membership takes effect at login, so log out and back in afterwards
('newgrp lp' covers a single shell). MODE="0666" needs neither the group nor the
re-login, at the cost of exposing the device to every local process.
EOF
    fi

    cat <<EOF

Do not reach for TAG+="uaccess", even though it is the usual modern mechanism
elsewhere: on NixOS the tag is set and nothing consumes it. The
RUN{builtin}+="uaccess" that installs the ACL ships in systemd's 71-seat.rules
and 73-seat-late.rules, neither of which NixOS assembles into
$UDEV_DIR — so the rule goes live and access is still denied.
EOF
}

print_next_steps() {
    local headline="Setup complete."
    local first="  1. Unplug and replug the PT-E920BT printer."

    if [[ "$GRANTED_ONE_OFF" == true ]]; then
        headline="One-off access granted."
        first="  1. Leave the printer plugged in — the grant is lost on replug."
    elif [[ "$ONE_OFF" == true ]]; then
        headline="Nothing changed."
        first="  1. Run the chmod above, and leave the printer plugged in afterwards."
    elif is_nixos; then
        headline="Nothing installed — on NixOS access is granted declaratively."
        first="  1. Add the rule above to your system configuration and rebuild, or
     re-run with --one-off for access until the next replug."
    fi

    cat <<EOF

$headline

Next steps:
$first
  2. Verify detection:
       brother-ptouch-driver discover
     (or: uv run brother-ptouch-driver discover)

For devcontainer and NixOS setup, troubleshooting, and manual steps see:
  docs/install/linux-usb.md
EOF
}

main() {
    parse_args "$@"
    require_linux
    require_sudo

    if [[ "$ONE_OFF" == true ]]; then
        grant_one_off || die "cannot grant access without a connected printer"
        print_next_steps
        return 0
    fi

    install_libusb

    if is_nixos; then
        # Not fatal: the declarative rule is worth printing even with the
        # printer unplugged.
        grant_one_off || true
        print_nixos_rule
    else
        install_udev_rule
        setup_plugdev
    fi

    print_next_steps
}

# Run only when executed, so the functions above can be sourced by tests. Under
# `curl | bash` BASH_SOURCE is empty and $0 is "bash", so the two still match and
# main runs; when sourced, BASH_SOURCE[0] is this file and $0 is the caller.
if [[ "${BASH_SOURCE[0]:-$0}" == "$0" ]]; then
    main "$@"
fi
