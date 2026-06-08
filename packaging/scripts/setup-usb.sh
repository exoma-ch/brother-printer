#!/usr/bin/env bash
# Install libusb and udev rules for non-root Brother PT-E920BT USB access on Linux.
#
# Run from a repository checkout or standalone (curl from GitHub):
#   ./packaging/scripts/setup-usb.sh
#   curl -fsSL https://raw.githubusercontent.com/exoma-ch/brother-printer/main/packaging/scripts/setup-usb.sh | bash
#
# For flags (--devcontainer, --ref, etc.) download first, then execute:
#   curl -fsSL .../setup-usb.sh -o setup-usb.sh && bash setup-usb.sh --devcontainer

set -euo pipefail

readonly REPO="exoma-ch/brother-printer"
readonly DEFAULT_REF="${REF:-main}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
readonly UDEV_DIR="/etc/udev/rules.d"

DEVCONTAINER=false
NO_LIBUSB=false
GIT_REF="$DEFAULT_REF"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Install libusb and udev rules for non-root Brother PT-E920BT USB access on Linux.

Options:
  --devcontainer   Install the devcontainer udev rule (MODE 0666) instead of
                   the standard host rule (0664 + plugdev). Skips plugdev setup.
  --no-libusb      Skip libusb prerequisite installation.
  --ref <git-ref>  Git ref for standalone udev rule download (default: $DEFAULT_REF).
                   Also settable via REF environment variable.
  -h, --help       Show this help and exit.

Examples:
  # From a repository checkout
  ./packaging/scripts/setup-usb.sh

  # Standalone (no flags via pipe; download first for options)
  curl -fsSL https://raw.githubusercontent.com/$REPO/main/packaging/scripts/setup-usb.sh | bash
  curl -fsSL https://raw.githubusercontent.com/$REPO/main/packaging/scripts/setup-usb.sh \\
    -o setup-usb.sh && bash setup-usb.sh --devcontainer
EOF
}

log() {
    echo "==> $*"
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

print_next_steps() {
    cat <<EOF

Setup complete.

Next steps:
  1. Unplug and replug the PT-E920BT printer.
  2. Verify detection:
       brother-ptouch-driver discover
     (or: uv run brother-ptouch-driver discover)

For devcontainer setup, troubleshooting, and manual steps see:
  docs/install/linux-usb.md
EOF
}

main() {
    parse_args "$@"
    require_linux
    require_sudo

    install_libusb
    install_udev_rule
    setup_plugdev
    print_next_steps
}

main "$@"
