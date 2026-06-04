#!/bin/bash

# Post-create script - runs once when container is created for the first time.
# This script is called from postCreateCommand in devcontainer.json.
#
# All one-time setup belongs here:
#   - Git repo init, config, hooks
#   - SSH key + allowed-signers placement
#   - GitHub CLI config + authentication
#   - Pre-commit hook installation
#   - Dependency sync (via just)

set -euo pipefail

echo "Running post-create setup..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/workspace/brother_printer"

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "Error: Project directory $PROJECT_ROOT does not exist"
    exit 1
fi

# Set venv prompt
sed -i 's/template-project/brother_printer/g' /root/assets/workspace/.venv/bin/activate

# Console scripts (e.g. brother-ptouch-driver) live in the pre-built venv but are not on PATH by default.
VENV_BIN="/root/assets/workspace/.venv/bin"
if [[ -d "$VENV_BIN" ]] && ! grep -qF "$VENV_BIN" /root/.bashrc 2>/dev/null; then
    cat >> /root/.bashrc <<EOF

# Project venv (brother-ptouch-driver and other console scripts)
export PATH="${VENV_BIN}:\$PATH"
EOF
fi

# One-time setup: git repo, config, hooks, gh auth
"$SCRIPT_DIR/init-git.sh"
"$SCRIPT_DIR/setup-git-conf.sh"
"$SCRIPT_DIR/setup-gh-repo.sh"
"$SCRIPT_DIR/init-precommit.sh"

# Sync dependencies (fast if nothing changed from pre-built venv)
echo "Syncing dependencies..."
just --justfile "$PROJECT_ROOT/justfile" --working-directory "$PROJECT_ROOT" sync

# User specific setup
# Add your custom setup commands here to install any dependencies or tools needed for your project

# PT-E920BT USB hardware verification needs the libusb backend (issue #4).
# pyusb talks to libusb-1.0 via ctypes; the base image does not ship it.
echo "Installing libusb backend for USB hardware tests..."
apt-get update && apt-get install -y --no-install-recommends libusb-1.0-0

echo "Post-create setup complete"
