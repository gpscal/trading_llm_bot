#!/bin/bash
# Uninstall Trading LLM Bot Dashboard systemd service

set -e

echo "Trading LLM Bot Dashboard Service Uninstallation Script"
echo "======================================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root to uninstall systemd service"
    echo "Please run: sudo $0"
    exit 1
fi

SYSTEMD_SERVICE="/etc/systemd/system/trading_llm_bot_dashboard.service"

# Check if service exists
if [ ! -f "$SYSTEMD_SERVICE" ]; then
    echo "Service file not found at $SYSTEMD_SERVICE"
    echo "Service may not be installed."
    exit 1
fi

# Stop service if running
if systemctl is-active --quiet trading_llm_bot_dashboard; then
    echo "Stopping trading_llm_bot_dashboard service..."
    systemctl stop trading_llm_bot_dashboard
fi

# Disable service if enabled
if systemctl is-enabled --quiet trading_llm_bot_dashboard 2>/dev/null; then
    echo "Disabling trading_llm_bot_dashboard service..."
    systemctl disable trading_llm_bot_dashboard
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

