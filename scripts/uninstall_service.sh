#!/bin/bash
# Uninstall SolBot systemd service

set -e

echo "SolBot Service Uninstallation Script"
echo "==================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root to uninstall systemd service"
    echo "Please run: sudo $0"
    exit 1
fi

SYSTEMD_SERVICE="/etc/systemd/system/solbot.service"

# Check if service exists
if [ ! -f "$SYSTEMD_SERVICE" ]; then
    echo "Service file not found at $SYSTEMD_SERVICE"
    echo "Service may not be installed."
    exit 1
fi

# Stop service if running
if systemctl is-active --quiet solbot; then
    echo "Stopping solbot service..."
    systemctl stop solbot
fi

# Disable service if enabled
if systemctl is-enabled --quiet solbot 2>/dev/null; then
    echo "Disabling solbot service..."
    systemctl disable solbot
fi

# Remove service file
echo "Removing service file..."
rm -f "$SYSTEMD_SERVICE"

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo ""
echo "Uninstallation complete!"
echo "Service has been removed from systemd."

