#!/bin/bash
# Create a systemd service for running SolBot simulation
# This runs the simulation independently of the web server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_NAME="solbot-simulation"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
VENV_DIR="$PROJECT_ROOT/venv"
USER=$(whoami)

echo "SolBot Simulation Service Setup"
echo "================================"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run with sudo"
    echo "Please run: sudo $0"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    exit 1
fi

echo "Creating systemd service file..."
echo ""

# Create the service file
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=SolBot Trading Simulation
After=network.target solbot.service
Requires=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_ROOT
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$PROJECT_ROOT"

# Load environment variables from .env file if it exists
EnvironmentFile=-$PROJECT_ROOT/.env

# Run the simulation script with default parameters
# Edit this line to customize initial balances:
ExecStart=$VENV_DIR/bin/python $PROJECT_ROOT/simulate.py --initial_balance_usdt 1000 --initial_balance_sol 10

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=solbot-sim

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

chmod 644 "$SERVICE_FILE"

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo ""
echo "Installation complete!"
echo ""
echo "Service file created at: $SERVICE_FILE"
echo ""
echo "To start the simulation service:"
echo "  sudo systemctl start $SERVICE_NAME"
echo ""
echo "To enable service to start on boot (optional):"
echo "  sudo systemctl enable $SERVICE_NAME"
echo ""
echo "To check service status:"
echo "  sudo systemctl status $SERVICE_NAME"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "To stop the service:"
echo "  sudo systemctl stop $SERVICE_NAME"
echo ""
echo "To restart the service:"
echo "  sudo systemctl restart $SERVICE_NAME"
echo ""
echo "To edit the service (e.g., to change simulation parameters):"
echo "  sudo nano $SERVICE_FILE"
echo "  # After editing, run: sudo systemctl daemon-reload"
echo "  # Then: sudo systemctl restart $SERVICE_NAME"
