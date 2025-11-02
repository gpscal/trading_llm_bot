#!/bin/bash
# Create a systemd user service for running simulations
# This allows simulations to run persistently even when disconnected

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_NAME="solbot-simulation"
USER_SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$USER_SERVICE_DIR/${SERVICE_NAME}.service"
VENV_DIR="$PROJECT_ROOT/venv"

echo "SolBot Simulation Service Setup"
echo "==============================="
echo ""

# Check if running as regular user (not root)
if [ "$EUID" -eq 0 ]; then 
    echo "Error: This script should NOT be run as root"
    echo "Please run as your regular user (without sudo)"
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

echo "Creating user systemd service directory..."
mkdir -p "$USER_SERVICE_DIR"

echo "Creating service file..."

# Create the service file
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=SolBot Trading Simulation
After=network.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_ROOT
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$PROJECT_ROOT"

# Load environment variables from .env file if it exists
EnvironmentFile=-$PROJECT_ROOT/.env

# Run the simulation script
# You can customize these arguments as needed
ExecStart=$VENV_DIR/bin/python $PROJECT_ROOT/simulate.py

# Restart policy
Restart=on-failure
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=solbot-sim

# Security
NoNewPrivileges=true

[Install]
WantedBy=default.target
EOF

chmod 644 "$SERVICE_FILE"

# Reload systemd user daemon
echo "Reloading systemd user daemon..."
systemctl --user daemon-reload

echo ""
echo "Installation complete!"
echo ""
echo "Service file created at: $SERVICE_FILE"
echo ""
echo "To start the simulation service:"
echo "  systemctl --user start $SERVICE_NAME"
echo ""
echo "To enable service to start on login (optional):"
echo "  systemctl --user enable $SERVICE_NAME"
echo ""
echo "To check service status:"
echo "  systemctl --user status $SERVICE_NAME"
echo ""
echo "To view logs:"
echo "  journalctl --user -u $SERVICE_NAME -f"
echo ""
echo "To stop the service:"
echo "  systemctl --user stop $SERVICE_NAME"
echo ""
echo "To edit the service (e.g., to change simulation parameters):"
echo "  nano $SERVICE_FILE"
echo "  # After editing, run: systemctl --user daemon-reload"
echo ""
echo "Note: To customize simulation parameters, edit the ExecStart line"
echo "in the service file. For example:"
echo "  ExecStart=$VENV_DIR/bin/python $PROJECT_ROOT/simulate.py --initial_balance_usdt 2000 --initial_balance_sol 20"
echo ""