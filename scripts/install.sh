#!/usr/bin/env bash
set -Eeuo pipefail

# Beep It Installation Script for Raspberry Pi
# This script sets up the Beep It application to run on startup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_DIR="/opt/beep_it"
SYSTEMD_DIR="/etc/systemd/system"
DEFAULT_DIR="/etc/default"

log() { printf "[install] %s\n" "$*"; }
error() { printf "[ERROR] %s\n" "$*" >&2; exit 1; }

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null && [[ "${FORCE_INSTALL:-}" != "1" ]]; then
    error "This script is designed for Raspberry Pi. Set FORCE_INSTALL=1 to override."
fi

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root (use sudo)"
fi

log "Installing Beep It application..."

# Create installation directory
log "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Install application
log "Installing application files..."
install -m 0755 "$REPO_ROOT/scan_gui.py" "$INSTALL_DIR/scan_gui.py"

# Create initial VERSION file
if [[ -f "$REPO_ROOT/updates/VERSION" ]]; then
    install -m 0644 "$REPO_ROOT/updates/VERSION" "$INSTALL_DIR/VERSION"
else
    echo "0.0.0" > "$INSTALL_DIR/VERSION"
fi

# Install Python dependencies
log "Installing Python dependencies..."
if [[ -f "$REPO_ROOT/requirements.txt" ]]; then
    pip3 install -r "$REPO_ROOT/requirements.txt" || error "Failed to install Python dependencies"
else
    log "WARNING: requirements.txt not found, installing known dependencies..."
    pip3 install psycopg2-binary
fi

# Install systemd service for the application
log "Installing systemd service: beep-it.service"
install -m 0644 "$REPO_ROOT/contrib/systemd/beep-it.service" "$SYSTEMD_DIR/beep-it.service"

# Install update script and systemd units
log "Installing auto-update mechanism..."
install -m 0755 "$REPO_ROOT/scripts/beep-it-update" "/usr/local/sbin/beep-it-update"
install -m 0644 "$REPO_ROOT/contrib/systemd/beep-it-update.service" "$SYSTEMD_DIR/beep-it-update.service"
install -m 0644 "$REPO_ROOT/contrib/systemd/beep-it-update.timer" "$SYSTEMD_DIR/beep-it-update.timer"

# Configure environment for updater
if [[ ! -f "$DEFAULT_DIR/beep-it-update" ]]; then
    log "Creating environment file for auto-updater..."
    cat > "$DEFAULT_DIR/beep-it-update" <<'EOF'
# GitHub Personal Access Token (read-only) for fetching private releases
# Generate one at: https://github.com/settings/tokens
# Required scope: repo (read-only access to private repositories)
GITHUB_TOKEN_RO=
EOF
    log "WARNING: You must set GITHUB_TOKEN_RO in $DEFAULT_DIR/beep-it-update"
fi

# Reload systemd
log "Reloading systemd daemon..."
systemctl daemon-reload

# Enable and start the application service
log "Enabling beep-it.service to start on boot..."
systemctl enable beep-it.service

# Enable the update timer (but don't start it yet - user needs to configure token first)
log "Enabling beep-it-update.timer..."
systemctl enable beep-it-update.timer

log ""
log "=============================================="
log "Installation complete!"
log "=============================================="
log ""
log "Next steps:"
log "1. Edit $DEFAULT_DIR/beep-it-update and add your GitHub token"
log "2. Start the application: sudo systemctl start beep-it.service"
log "3. Start the update timer: sudo systemctl start beep-it-update.timer"
log ""
log "Useful commands:"
log "  - Check app status:    sudo systemctl status beep-it.service"
log "  - View app logs:       sudo journalctl -u beep-it.service -f"
log "  - Restart app:         sudo systemctl restart beep-it.service"
log "  - Check update timer:  sudo systemctl list-timers beep-it-update.timer"
log "  - Manual update:       sudo systemctl start beep-it-update.service"
log ""
