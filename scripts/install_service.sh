#!/bin/bash
# Install SolBot systemd service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_FILE="$PROJECT_ROOT/solbot.service"
SYSTEMD_SERVICE="/etc/systemd/system/solbot.service"
VENV_DIR="$PROJECT_ROOT/venv"
LOG_DIR="$PROJECT_ROOT/logs"

echo "SolBot Service Installation Script"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root to install systemd service"
    echo "Please run: sudo $0"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Warning: Virtual environment not found at $VENV_DIR"
    echo "Please create it first: python3 -m venv venv"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get current user (from the user who invoked sudo)
INSTALL_USER="${SUDO_USER:-$USER}"
INSTALL_GROUP="$(id -gn $INSTALL_USER)"

echo "Installing service for user: $INSTALL_USER"
echo "Project root: $PROJECT_ROOT"
echo ""

# Create log directory
echo "Creating log directory..."
mkdir -p "$LOG_DIR"
chown "$INSTALL_USER:$INSTALL_GROUP" "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Replace placeholders in service file
echo "Configuring service file..."
VENV_BIN="$VENV_DIR/bin"
sed -e "s|%USER%|$INSTALL_USER|g" \
    -e "s|%GROUP%|$INSTALL_GROUP|g" \
    -e "s|%PROJECT_ROOT%|$PROJECT_ROOT|g" \
    -e "s|%VENV_BIN%|$VENV_BIN|g" \
    "$SERVICE_FILE" > /tmp/solbot.service.tmp

# Copy service file to systemd
echo "Installing systemd service file..."
cp /tmp/solbot.service.tmp "$SYSTEMD_SERVICE"
chmod 644 "$SYSTEMD_SERVICE"
rm /tmp/solbot.service.tmp

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo ""
echo "Installation complete!"
echo ""
echo "To start the service:"
echo "  sudo systemctl start solbot"
echo ""
echo "To enable service to start on boot:"
echo "  sudo systemctl enable solbot"
echo ""
echo "To check service status:"
echo "  sudo systemctl status solbot"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u solbot -f"

