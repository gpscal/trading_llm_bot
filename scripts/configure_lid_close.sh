#!/bin/bash
# Configure systemd-logind to prevent suspend when laptop lid closes
# This allows simulations and services to continue running when lid is closed

set -e

echo "Configuring systemd-logind to prevent suspend on lid close"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root"
    echo "Please run: sudo $0"
    exit 1
fi

LOGIND_CONF="/etc/systemd/logind.conf"
BACKUP_CONF="${LOGIND_CONF}.backup.$(date +%Y%m%d_%H%M%S)"

# Create backup
if [ -f "$LOGIND_CONF" ]; then
    echo "Creating backup of existing config: $BACKUP_CONF"
    cp "$LOGIND_CONF" "$BACKUP_CONF"
fi

# Create or modify logind.conf
echo "Configuring logind.conf..."

# Check if file exists, if not create it
if [ ! -f "$LOGIND_CONF" ]; then
    touch "$LOGIND_CONF"
fi

# Function to set or update a config option
set_config() {
    local key="$1"
    local value="$2"
    
    if grep -q "^#*${key}=" "$LOGIND_CONF"; then
        # Key exists, update it
        sed -i "s|^#*${key}=.*|${key}=${value}|" "$LOGIND_CONF"
        echo "  Updated: ${key}=${value}"
    else
        # Key doesn't exist, add it
        echo "${key}=${value}" >> "$LOGIND_CONF"
        echo "  Added: ${key}=${value}"
    fi
}

# Configure lid switch settings
set_config "HandleLidSwitch" "ignore"
set_config "HandleLidSwitchExternalPower" "ignore"
set_config "HandleLidSwitchDocked" "ignore"

# Restart systemd-logind to apply changes
echo ""
echo "Restarting systemd-logind service..."
systemctl restart systemd-logind

echo ""
echo "Configuration complete!"
echo ""
echo "The following settings have been applied:"
echo "  - HandleLidSwitch=ignore (closing lid won't suspend)"
echo "  - HandleLidSwitchExternalPower=ignore (ignores lid even when on AC power)"
echo "  - HandleLidSwitchDocked=ignore (ignores lid when docked)"
echo ""
echo "To revert these changes, restore from backup:"
echo "  sudo cp $BACKUP_CONF $LOGIND_CONF"
echo "  sudo systemctl restart systemd-logind"
echo ""
echo "To check current settings:"
echo "  cat $LOGIND_CONF | grep HandleLidSwitch"
echo ""